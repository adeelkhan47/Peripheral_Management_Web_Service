from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import usb.core
import usb.util
from escpos.printer import Usb

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Local Peripheral Management Service", description="A service to manage a local 80mm POS printer, a 4x6 label printer, and a USB postal scale.")

# Global configuration dictionary for devices
config = {
    "printer": {"vendorId": "0xXXXX", "productId": "0xYYYY", "copies": 1},
    "scale": {"vendorId": "0xAAAA", "productId": "0xBBBB", "unit": "grams"}
}

# Pydantic models for request validation
class PrintRequest(BaseModel):
    printerType: str
    content: str
    options: dict

class ScaleCommand(BaseModel):
    command: str

class ConfigurationRequest(BaseModel):
    printer: dict
    scale: dict

# Endpoint to print on the configured printer
@app.post("/print")
async def print_document(print_request: PrintRequest):
    """
    Endpoint to handle print requests.
    """
    global config
    printer_type = print_request.printerType

    # Use configured vendor/product IDs to interact with the printer
    vendor_id = int(config['printer']['vendorId'], 16)
    product_id = int(config['printer']['productId'], 16)

    # Initialize printer (using python-escpos for USB printers)
    try:
        printer = Usb(vendor_id, product_id)
        printer.text(print_request.content + "\n")
        printer.cut()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Printer error: {str(e)}")

    return {"message": "Print job completed successfully"}

# Endpoint to configure the printer and scale
@app.post("/configure")
async def configure_devices(config_request: ConfigurationRequest):
    """
    Endpoint to configure printer and scale settings.
    """
    global config
    config['printer'] = config_request.printer
    config['scale'] = config_request.scale
    return {"message": "Configuration updated successfully"}

# Endpoint to handle scale commands
@app.post("/scale")
async def handle_scale(scale_command: ScaleCommand):
    """
    Endpoint to handle commands for the USB postal scale.
    """
    global config
    # Use configured vendor/product IDs to interact with the USB scale
    vendor_id = int(config['scale']['vendorId'], 16)
    product_id = int(config['scale']['productId'], 16)

    dev = usb.core.find(idVendor=vendor_id, idProduct=product_id)
    if dev is None:
        raise HTTPException(status_code=400, detail="USB scale not found.")

    # Handle scale commands
    if scale_command.command == "scale":
        weight = 250.0  # Simulated weight (replace with actual scale reading)
        if config['scale']['unit'] == "ounces":
            weight /= 28.35  # Convert grams to ounces if needed
        return {"weight": weight}
    elif scale_command.command in ["tare", "reset"]:
        # Simulate scale reset/tare operation
        return {"message": f"Scale {scale_command.command} successful"}
    else:
        raise HTTPException(status_code=400, detail="Invalid scale command.")

# Error reporting endpoint (can be extended for actual remote reporting)
@app.post("/error-report")
async def error_report():
    """
    Simulated error reporting to a remote service (replace with actual reporting logic).
    """
    # Implement error reporting logic here (for printers or scales)
    return {"message": "Error reported successfully"}

# Example health check or status endpoint
@app.get("/status")
async def status():
    """
    Endpoint to check the actual status of the printer.
    """
    global config
    printer_status = "Unknown"
    scale_status = "Unknown"

    try:
        # Use configured vendor/product IDs to interact with the printer
        vendor_id = int(config['printer']['vendorId'], 16)
        product_id = int(config['printer']['productId'], 16)

        # Initialize the USB printer
        printer = Usb(vendor_id, product_id)

        # Check printer status using a direct call (DLE EOT status command may vary)
        status = printer.device.get_status()  # This is just a placeholder

        # Based on the response, interpret the status
        if status & 0x18 == 0x18:
            printer_status = "Paper End"
        elif status & 0x08 == 0x08:
            printer_status = "Paper Low"
        else:
            printer_status = "Ready"
    except usb.core.USBError as usb_err:
        raise HTTPException(status_code=500, detail=f"USB Error: {str(usb_err)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking printer status: {str(e)}")

    return {
        "printer": {"type": "POS", "status": printer_status},
        "scale": {"status": scale_status}  # You can implement similar status for scale here
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
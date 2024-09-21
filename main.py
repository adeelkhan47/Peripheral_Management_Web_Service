# Peripheral_Management_Web_Service
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import usb.core
import usb.util

app = FastAPI(title="Peripheral Management Service")

# Configuration storage for printer and scale
config = {
    "printer": {
        "type": "80mm",  # Default printer type
        "copies": 1,  # Default number of copies
        "orientation": "portrait"  # Default orientation
    },
    "scale": {
        "vendorId": None,  # USB vendor ID for the scale (hex string)
        "productId": None,  # USB product ID for the scale (hex string)
        "unit": "grams"  # Default unit for scale (grams or ounces)
    }
}


class PrintRequest(BaseModel):
    printerType: str
    content: str
    options: dict

class ScaleCommand(BaseModel):
    command: str

# Model for printer configuration
class PrinterConfig(BaseModel):
    type: str = "80mm"
    copies: int = 1
    orientation: str = "portrait"

# Model for scale configuration
class ScaleConfig(BaseModel):
    vendorId: str  # USB vendor ID for the scale in hex format (e.g., '0x1234')
    productId: str  # USB product ID for the scale in hex format (e.g., '0x5678')
    unit: str = "grams"  # Default unit for weight ('grams' or 'ounces')

# Model for configure request
class ConfigurationRequest(BaseModel):
    printer: PrinterConfig
    scale: ScaleConfig

@app.post("/configure")
async def configure_devices(config_request: ConfigurationRequest):
    """
    Endpoint to update the configuration for both the printer and USB scale.
    """
    global config
    # Update printer configuration
    config['printer'].update(config_request.printer)

    # Update scale configuration
    config['scale'].update(config_request.scale)

    # Check if the USB scale exists based on updated vendor and product IDs
    if config['scale']['vendorId'] and config['scale']['productId']:
        dev = usb.core.find(idVendor=int(config['scale']['vendorId'], 16),
                            idProduct=int(config['scale']['productId'], 16))
        if dev is None:
            raise HTTPException(status_code=400, detail="USB scale not found.")

    return {"message": "Configuration updated successfully"}


@app.post("/print")
async def print_document(print_request: PrintRequest):
    global printer
    if printer is None:
        raise HTTPException(status_code=400, detail="Printer not configured.")

    printer_type = print_request.printerType or config['printer']['type']
    copies = print_request.options.get('copies', config['printer']['copies'])
    orientation = print_request.options.get('orientation', config['printer']['orientation'])

    # Print the content for the specified number of copies
    for _ in range(copies):
        printer.text(print_request.content + "\n")
        printer.cut()  # Cut the paper after printing

    return {"jobID": "12345"}


@app.get("/status")
async def get_status():
    """
    Endpoint to return the status of the printers and scale.
    """
    global config
    # Simulated printer and scale statuses (replace with actual hardware checks)
    printers_status = [
        {
            "type": config['printer']['type'],
            "status": "ready",
            "errorMessage": None
        }
    ]

    scale_status = {
        "status": "ready",
        "errorMessage": None,
        "weight": 0.0  # Default weight (replace with actual scale reading)
    }

    return {
        "printers": printers_status,
        "scale": scale_status
    }


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


@app.post("/error-report")
async def error_report():
    """
    Simulated error reporting to a remote service (replace with actual reporting logic).
    """
    # Implement error reporting logic here (for printers or scales)
    return {"message": "Error reported successfully"}

# Run FastAPI app
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

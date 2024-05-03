import win32com.client

# Create a new instance of BarTender
bt_app = win32com.client.Dispatch("BarTender.Application")

# Open the BarTender print dialog
bt_app.Visible = True

# Open the label format
label_format = bt_app.Formats.Open("C:\\python\\label_printing\\template.btw", False, "")

# Set the image
image_object = label_format.Objects("Рисунок 1")  # Replace with your image object name in the template
image_object.FileName = "C:\\python\\label_printing\\stickers\\1669753373.png"

# Select the printer
label_format.PrintSetup.PrinterName = "YourPrinterName"  # Replace with your printer name

# Print the label
label_format.PrintOut(False, False)

# Close BarTender
bt_app.Quit(1)
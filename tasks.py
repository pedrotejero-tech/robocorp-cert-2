from robocorp.tasks import task
from robocorp import browser

from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    browser.configure(
        slowmo=100,
    )
    open_robot_order_website()
    download_orders_file()
    process_orders()


def open_robot_order_website():
    """Navigates to the given URL"""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")
    page = browser.page()
    page.click("button:text('OK')")

def download_orders_file():
    """Downloads orders file from the given URL"""
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)

def fill_order_form(order):
    """Fills in the order form and take a screenshot of the page"""
    page = browser.page()
    if page.is_visible("text=OK"):
        page.click("text=OK")

    page.select_option("#head", order["Head"])
    page.check(f"#id-body-{order['Body']}")
    page.fill('input[placeholder="Enter the part number for the legs"]', str(order["Legs"]))
    page.fill("#address", order["Address"])
    page.click("text=Preview")

def store_receipt_as_pdf(order_number):
    """Saves the order HTML receipt as a PDF file"""
    page = browser.page()

    receipt = page.locator("#receipt")

    # Wait until receipt is actually present
    receipt.wait_for(state="attached", timeout=3000)

    # Get FULL HTML (not just inner)
    receipt_html = receipt.evaluate("el => el.outerHTML")

    # Wrap in a minimal HTML document (important for PDF rendering)
    full_html = f"""
    <html>
        <body>
            {receipt_html}
        </body>
    </html>
    """

    pdf = PDF()
    pdf.html_to_pdf(full_html, f"output/receipts/receipt_{order_number}.pdf")


def screenshot_robot(order_number):
    """Takes a screenshot of the robot preview image"""
    page = browser.page()

    robot = page.locator("#robot-preview-image")

    # Ensure the robot is visible
    robot.wait_for(state="visible", timeout=5000)

    screenshot_path = f"output/screenshots/robot_{order_number}.png"

    robot.screenshot(path=screenshot_path)

    return screenshot_path

def embed_screenshot_to_receipt(screenshot, pdf_file):
    """Append the robot screenshot to the existing receipt PDF."""
    pdf = PDF()

    pdf.add_files_to_pdf(
        files=[screenshot],
        target_document=pdf_file,
        append=True
    )

def process_orders():
    """Reads the orders file and processes the orders"""
    library = Tables()
    orders = library.read_table_from_csv(
        "orders.csv", header=True, columns=["Order number", "Head", "Body", "Legs", "Address"]
        )

    for order in orders:
        fill_order_form(order)
        
        max_attempts = 5
        attempts = 0

        while attempts < max_attempts:
            page = browser.page()
            page.click("#order")

            try:
                page.wait_for_selector("#receipt", timeout=2000)
                break
            except:
                print("Retrying order...")
                attempts += 1

        if attempts == max_attempts:
            raise Exception("Order failed too many times")

        store_receipt_as_pdf(order["Order number"])
        screenshot_path = screenshot_robot(order["Order number"])
        pdf_file = f"output/receipts/receipt_{order['Order number']}.pdf"
        embed_screenshot_to_receipt(screenshot_path, pdf_file)

        page = browser.page()
        page.click("#order-another")
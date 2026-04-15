from robocorp.tasks import task
from robocorp import browser

from RPA.HTTP import HTTP
from RPA.Tables import Tables

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

    page.select_option("#head", order["Head"])
    page.check(f"#id-body-{order['Body']}")
    page.fill('input[placeholder="Enter the part number for the legs"]', str(order["Legs"]))
    page.fill("#address", order["Address"])
    page.click("text=Preview")

    page.screenshot(
        path=f"output/screenshots/order_{order['Order number']}.png",
        full_page=True
        )

def process_orders():
    """Reads the orders file and processes the orders"""
    library = Tables()
    orders = library.read_table_from_csv(
        "orders.csv", header=True, columns=["Order number", "Head", "Body", "Legs", "Address"]
        )

    for order in orders:
        fill_order_form(order)
        flag = False
        while not flag:
            page = browser.page()
            page.click("text=ORDER")
            if not page.is_visible("text=Error:"):
                flag = True

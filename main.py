from datetime import datetime, time
from zoneinfo import ZoneInfo
from threading import Timer
import subprocess
import sys
import ctypes
import asyncio
import functools
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def set_chrome_settings():
    chrome_options = Options()
    args = [
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-sync",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-client-side-phishing-detection",
        "--disable-default-apps",
        "--disable-hang-monitor",
        "--disable-popup-blocking",
        "--disable-prompt-on-repost",
        "--disable-translate",
        "--disable-infobars",
        "--metrics-recording-only",
        "--no-first-run",
        "--safebrowsing-disable-auto-update",
        "--mute-audio",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage"
    ]

    for arg in args:
        chrome_options.add_argument(arg)

    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.fonts": 2,
        "profile.managed_default_content_settings.plugins": 2,
        "profile.managed_default_content_settings.popups": 2,
        "profile.managed_default_content_settings.geolocation": 2,
        "profile.managed_default_content_settings.notifications": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)

    chrome_service = Service(ChromeDriverManager().install())
    chrome_service.creation_flags = 0x8000000  # Suppress logs

    return chrome_service, chrome_options

def run_as_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("This script needs to be run as Administrator. Re-launching with elevated privileges...")
        # Relaunch the script with admin rights
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()  # Exit the original script

def sync_windows_time():
    try:
        # Start the Windows Time service if it's not running
        subprocess.run(["net", "start", "w32time"], shell = True, check = False)

        # Resync time
        subprocess.run(["w32tm", "/resync"], shell = True, check = True)
        print("Time successfully synchronized with Windows Time Server.")

    except subprocess.CalledProcessError as e:
        print("Error syncing time. Please run this program as Administrator.", e)

async def periodic_label_injection(driver, term_label):
    while True:
        try:
            driver.execute_script("""
            if (!document.getElementById("__term_label__")) {
                let label = document.createElement('div');
                label.id = "__term_label__";
                label.innerText = arguments[0];
                label.style.position = 'fixed';
                label.style.top = '10px';
                label.style.right = '10px';
                label.style.padding = '8px 12px';
                label.style.backgroundColor = 'red';
                label.style.color = 'white';
                label.style.fontSize = '28px';
                label.style.zIndex = 9999;
                document.body.appendChild(label);
            }
            """, term_label)
        except Exception as e:
            print("Error injecting label:", e)
        await asyncio.sleep(1)  # Wait before trying to inject again

async def main():
    # Running the script as Administrator is required for syncing the time
    run_as_admin()

    # Get screen dimensions
    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)

    # Initialize ChromeDriver with optimizations
    chrome_service, chrome_options = set_chrome_settings()
    driver1 = webdriver.Chrome(service = chrome_service, options = chrome_options)
    driver1.set_window_rect(0, 0, screen_width / 2, screen_height)
    driver1.get("https://wd10.myworkday.com/ubc/d/home.htmld")
    driver2 = webdriver.Chrome(service = chrome_service, options = chrome_options)
    driver2.set_window_rect(screen_width / 2, 0, screen_width / 2, screen_height)
    driver2.get("https://wd10.myworkday.com/ubc/d/home.htmld")
    asyncio.create_task(periodic_label_injection(driver1, "Term 1"))
    asyncio.create_task(periodic_label_injection(driver2, "Term 2"))

    # Wait until exactly the course registration time in PST (24-hour time)
    pst_tz = ZoneInfo("America/Los_Angeles")
    year = datetime.now(pst_tz).year
    month = datetime.now(pst_tz).month
    day = datetime.now(pst_tz).day
    second = 0
    microsecond = 0
    ### MODIFY TO MATCH YOUR COURSE REGISTRATION TIME IN PST (24-hour time) ###
    hour = #
    minute = #

    reg_time = time(hour, minute)
    form_reg_time = reg_time.strftime("%I:%M %p").lstrip("0").lower()  # Formatted as 12-hour time
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        functools.partial(
            input,
            f"Welcome to UBC Dual-Term Course Sniper!\nInstructions:\n 1. ⭐ENSURE YOUR COURSE REGISTRATION TIME (PST) IS SET CORRECTLY!⭐\n"
            f"    You have set your course registration time to {form_reg_time} PST.\n"
            f" 2. Manually log in to UBC Workday with your CWL in both windows.\n"
            f" 3. Open two Saved Schedules IN THE CORRESPONDING \"TERM\" WINDOWS (see top-right of page).\n"
            f" 4. Press `Enter` in the terminal to start the script."
        )
    )

    sync_windows_time()

    target_time = datetime(year, month, day, hour, minute, second, microsecond, pst_tz)
    now = datetime.now(pst_tz)
    if now > target_time:
        print(f"\nIt is past {form_reg_time}.")
    else:
        wait_seconds = (target_time - now).total_seconds()
        initial_refresh_seconds = wait_seconds - 15.000
        Timer(initial_refresh_seconds, driver1.refresh).start()  # Preemptive refreshes for page caching
        Timer(initial_refresh_seconds, driver2.refresh).start()
        print(f"\nWaiting {wait_seconds:.3f} seconds until {form_reg_time}.\nThe page will refresh 15 seconds before the target time.\nDO NOT TOUCH YOUR COMPUTER except to ensure that it does not fall asleep.")
        await asyncio.sleep(wait_seconds)

    # Refresh Term 1 page at the target time
    print("\nTarget time reached. Refreshing Term 1 page...")
    driver1.refresh()

    # Register Term 1
    try:
        register_button = WebDriverWait(driver1, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Start Registration')]")))
        register_button.click()
        print("\nClicked 'Start Registration' [Term 1]")

        confirm_register_button = WebDriverWait(driver1, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Register')]")))
        confirm_register_button.click()
        print("\nClicked 'Register' [Term 1]")

    except Exception:
        input("\nERROR FINDING/CLICKING REGISTRATION BUTTONS [Term 1]. Press `Enter` to exit.")
        driver1.quit()
        driver2.quit()
        sys.exit()

    # Wait for Term 1 registration to complete
    try:
        WebDriverWait(driver1, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Successful Registrations')]"))
        )
    except Exception:
        input("\nError finding 'Successful Registrations' [Term 1]. Press `Enter` to proceed with Term 2 registration.")

    # Refresh Term 2 page immediately after
    print("\nRefreshing Term 2 page...")
    driver2.refresh()

    # Register Term 2
    try:
        register_button = WebDriverWait(driver2, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Start Registration')]")))
        register_button.click()
        print("\nClicked 'Start Registration' [Term 2]")

        confirm_register_button = WebDriverWait(driver2, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Register')]")))
        confirm_register_button.click()
        print("\nClicked 'Register' [Term 2]")

        # Check if Term 2 registration is complete
        try:
            WebDriverWait(driver1, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Successful Registrations')]"))
            )
            print("\nCourse registration successful. Close Chrome and the terminal to exit.")

        except Exception:
            input("\nError finding 'Successful Registrations' [Term 2]. Press `Enter` to exit.")
            driver1.quit()
            driver2.quit()
            sys.exit()

    except Exception:
        input("\nERROR FINDING/CLICKING REGISTRATION BUTTONS [Term 2]. Press `Enter` to exit.")
        driver1.quit()
        driver2.quit()
        sys.exit()

    await asyncio.sleep(999999) # Keep Chrome open (for ~11 days)

    # Cleanup (optional)
    # driver.quit()

if __name__ == "__main__":
    asyncio.run(main())
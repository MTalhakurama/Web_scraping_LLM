import os
import agentql
from playwright.sync_api import sync_playwright
from pyairtable import Api
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
AGENTQL_API_KEY = os.getenv("AGENTQL_API_KEY")
print("AGENTQL_API_KEY:", AGENTQL_API_KEY)
print("EMAIL:", EMAIL)
print("PASSWORD:", PASSWORD)

os.environ["AGENTQL_API_KEY"] = AGENTQL_API_KEY

INITIAL_URL = "https://www.idealist.org/"

JOB_POSTS_QUERY = """
{
    job_posts {
        title
        organization
        salary
        location
        contract_type(contract full time)
        location_type(remote or on-site or hybrid)
        date_posted
    }
}
"""

PAGINATION_QUERY = """
{
    pagination {
        next_page_btn
    }
}
"""

EMAIL_INPUT_QUERY = """
{
    login_form {
        email_input
    }
}
"""

VERIFY_QUERY = """
{
    login_form {
        verify_not_robot_checkbox
    }
}
"""

PASSWORD_INPUT_QUERY = """
{
    login_form {
        password_input
        continue_btn
    }
}
"""

def login(page):
    response = page.query_elements(EMAIL_INPUT_QUERY)
    if response and response.login_form and response.login_form.email_input:
        response.login_form.email_input.fill(EMAIL)
        page.wait_for_timeout(10000)

    verify_response = page.query_elements(VERIFY_QUERY)
    if verify_response and verify_response.login_form and verify_response.login_form.verify_not_robot_checkbox:
        verify_response.login_form.verify_not_robot_checkbox.click()
    else:
        print("Could not locate verify_not_robot_checkbox.")
    
    page.wait_for_timeout(10000)

    password_response = page.query_elements(PASSWORD_INPUT_QUERY)
    if password_response and password_response.login_form and password_response.login_form.password_input:
        password_response.login_form.password_input.fill(PASSWORD)
        password_response.login_form.continue_btn.click()
        page.wait_for_timeout(10000)

def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(storage_state="idealist_login.json" if os.path.exists("idealist_login.json") else None)
        
        page = agentql.wrap(context.new_page())
        page.goto(INITIAL_URL)

        if not os.path.exists("idealist_login.json"):
            print("No login found, logging in")
            login(page)
            context.storage_state(path="idealist_login.json")
        
        status = True
        while status:
            current_url = page.url
            
            jobs_post_response = page.query_elements(JOB_POSTS_QUERY)
            jobs_post_data = jobs_post_response.job_posts.to_data() if jobs_post_response and jobs_post_response.job_posts else []
            
            print(f"Total jobs found: {len(jobs_post_data)}")
            print(jobs_post_data)
            
            pagination = page.query_elements(PAGINATION_QUERY)
            next_page_btn = pagination.pagination.next_page_btn if pagination and pagination.pagination else None
            
            if next_page_btn:
                next_page_btn.click()
                page.wait_for_load_state("load")
            else:
                status = False
            
            if current_url == page.url:
                status = False

        page.close()
        browser.close()

if __name__ == "__main__":
    main()

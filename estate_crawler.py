from playwright.sync_api import sync_playwright
import time
import csv
import json

max_pages = 10  # Number of pages to scrape
scraped_data = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # Go to the initial listing page
    page.goto("https://nigeriapropertycentre.com/for-sale/houses/lagos", wait_until="load", timeout=60000)
    time.sleep(5)

    for page_num in range(max_pages):
        print(f"\n📄 Scraping page {page_num + 1}...\n")

        # Wait for listings to load
        page.wait_for_selector('div.col-md-12 div.wp-block.property.list', timeout=30000)
        listings = page.query_selector_all('div.col-md-12 div.wp-block.property.list')

        for listing in listings:
            # Extract main details
            title_elem = listing.query_selector('h4.content-title')
            title = title_elem.inner_text().replace("\xa0", " ").strip() if title_elem else "N/A"

            price_elem = listing.query_selector('span.pull-sm-left')
            price = price_elem.inner_text().replace("\xa0", " ").strip() if price_elem else "N/A"

            location_elem = listing.query_selector('address.voffset-bottom-10 > strong')
            location = location_elem.inner_text().replace("\xa0", " ").strip() if location_elem else "N/A"

            # Extract listing URL and image
            url = listing.query_selector('a[itemprop="url"]').get_attribute('href')
            full_url = f"https://nigeriapropertycentre.com{url}"

            image_elem = listing.query_selector('img[itemprop="image"]')
            image_url = image_elem.get_attribute('src') if image_elem else "N/A"

            # Extract bedroom, bathroom, and toilet info
            footer = listing.query_selector('div.wp-block-footer')
            property_details = {"beds": "N/A", "baths": "N/A", "toilets": "N/A"}

            if footer:
                items = footer.query_selector_all('ul.aux-info li')
                for item in items:
                    spans = item.query_selector_all('span')
                    if len(spans) >= 2:
                        number = spans[0].inner_text().replace("\xa0", " ").strip()
                        label = spans[1].inner_text().replace("\xa0", " ").strip().lower()
                        if "bedroom" in label:
                            property_details["beds"] = number
                        elif "bathroom" in label:
                            property_details["baths"] = number
                        elif "toilet" in label:
                            property_details["toilets"] = number

            # Extract agent and phone number
            agent_span = listing.query_selector('span.marketed-by.pull-right')
            if agent_span:
                full_text = agent_span.inner_text().replace("\xa0", " ").strip()
                phone_elem = agent_span.query_selector('strong')
                phone_number = phone_elem.inner_text().replace("\xa0", " ").strip() if phone_elem else "N/A"
                if not phone_number.replace(" ", "").replace("-", "").isdigit():
                    phone_number = "N/A"
                agent_name = full_text.replace(phone_number, "").strip() if phone_number != "N/A" else full_text.strip()
            else:
                agent_name = "N/A"
                phone_number = "N/A"

            # Store listing data
            data = {
                "title": title,
                "price": price,
                "location": location,
                "bedrooms": property_details["beds"],
                "bathrooms": property_details["baths"],
                "toilets": property_details["toilets"],
                "agent_name": agent_name,
                "phone": phone_number,
                "image_url": image_url,
                "url": full_url
            }

            scraped_data.append(data)

            # Debug print
            print(f"🏠 {title}")
            print(f"💰 {price}")
            print(f"📍 {location}")
            print(f"🛏️ Bedrooms: {property_details['beds']}")
            print(f"🛁 Bathrooms: {property_details['baths']}")
            print(f"🚽 Toilets: {property_details['toilets']}")
            print(f"👤 Agent: {agent_name}")
            print(f"📞 Phone: {phone_number}")
            print(f"🖼️ Image: {image_url}")
            print(f"🔗 URL: {full_url}")
            print("---")

        # Move to next page
        next_button = page.query_selector('div.pPagination a[rel*="next"]')
        if next_button:
            next_button.click()
            time.sleep(5)  # Wait for next page
        else:
            print("🚫 No more pages.")
            break

    # Save as JSON
    with open("properties.json", "w", encoding="utf-8") as json_file:
        json.dump(scraped_data, json_file, ensure_ascii=False, indent=4)

    # Save as CSV (Excel-friendly encoding)
    with open("properties.csv", "w", newline='', encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=scraped_data[0].keys())
        writer.writeheader()
        writer.writerows(scraped_data)

    input("✅ Done scraping. Press Enter to close browser...")
    browser.close()


# -*- coding: utf-8 -*-

import os
import time
import sys
import webkit_server

IMAGE_LOAD_ATTEMPTS = 5

def fill_element(element, value):
    if value:
        # Funny trick for multiline string
        element.eval_script("""
            var valueString = function(){{/*{}*/}}.toString().slice(15,-4);
            node.value = valueString;
            var event = document.createEvent("HTMLEvents");
            event.initEvent("change", true, true);
            node.dispatchEvent(event);
        """.format(value))

def fill(elements, values):
    for i, value in enumerate(values):
        if value:
            fill_element(elements[i], value)


class GooglePlay(object):
    def __init__(self, app, username, password, debug_dir=None):
        self.app = app
        self.username = username
        self.password = password
        self.debug_dir = debug_dir

        self.session = webkit_server.Client()
  
        if self.debug_dir:
            if not os.path.exists(self.debug_dir):
                os.mkdir(self.debug_dir)

    # Publication process
    def publish(self):
        self.store_locale()

        self.session.visit("https://play.google.com/apps/publish/v2/")
        self._debug("developer_console", "opened")

        self.login()
        
        # Select All applications menu
        xpath = "//sidebar/nav/ul/li/a/div"
        self.session.at_xpath(xpath).click()
        
        if self.ensure_application_listed():
            self.open_app()
        else:
            self.create_app()

        self.fill_store_listing()
        self.upload_apk()
        self.fill_pricing_and_distribution()

        self.restore_locale()

    # Checks
    def ensure_all_applications_header(self):
        xpath = "//h2[normalize-space(text()) = 'All applications']"
        return self._ensure(xpath)

    def ensure_application_listed(self):
        xpath = "//section/div/table/tbody/tr/td/div/a/span[contains(text(), '{}')]"
        return self._ensure(xpath.format(self.app.title()))

    def ensure_application_header(self):
        xpath = "//h2/span[contains(text(), '{}')]".format(self.app.title())
        return self._ensure(xpath)

    def ensure_store_listing_header(self):
        xpath = "//h3[contains(text(), 'Store Listing')]"
        return self._ensure(xpath)

    def ensure_saved_message(self):
        xpath = "//*[normalize-space(text()) = 'Saved']"
        return self._ensure(xpath)

    def ensure_add_language_header(self):
        xpath = "//"
        return self._ensure(xpath)
    
    def _ensure(self, xpath):
        return self.session.at_xpath(xpath, timeout=10)

    # Actions

    def open_account(self):
        self.session.visit("https://accounts.google.com/ServiceLogin")
        self._debug("account_settings", "opened")

    def store_locale(self):
        self.open_account()
        self.login()
        # Store current language
        xpath = "//body/div[4]/div[2]/div[1]/div[1]/div/div/div/div[1]/div/div[3]/div/div/div[3]/div[2]/div/div[1]/div[1]"
        self.locale = self.session.at_xpath(xpath).text()
        
        xpath = "//body/div[4]/div[2]/div[1]/div[1]/div/div/div/div[1]/div/div[3]/div/div/div[3]/div[2]/div/div[1]/div[2]/a"
        self.session.at_xpath(xpath).click()
        
        xpath = "//div[@role=\"dialog\"]/div[2]/div/div/div/span[contains(text(), \"English (United States)\")]"
        self.session.at_xpath(xpath).click()
        self._debug("locale", "changed")
        
    def restore_locale(self):
        self.open_account()
        self.login()
        # Restore previous language
        xpath = "//body/div[4]/div[2]/div[1]/div[1]/div/div/div/div[1]/div/div[3]/div/div/div[3]/div[2]/div/div[1]/div[2]/a"
        self.session.at_xpath(xpath).click()
        
        xpath = "//div[@role=\"dialog\"]/div[2]/div/div/div[count(span[contains(text(), \"{}\")])=1]".format(self.locale)
        self.session.at_xpath(xpath).click()
        self._debug("locale", "restored")

    def login(self):
        login_url = "https://accounts.google.com/ServiceLogin"

        if self.session.url().startswith(login_url):
            email_field = self.session.at_css("#Email")
            password_field = self.session.at_css("#Passwd")
            if email_field.get_attr("class") != "hidden":
                email_field.set(self.username)
            password_field.set(self.password)
            self._debug("login", "filled")
            
            email_field.form().submit()
            self._debug("login", "submited")
            if self.session.url().startswith(login_url):
                print "Login error"
                sys.exit(1)

    def open_app(self):
        xpath = "//section/div/table/tbody/tr/td/div/a/span[contains(text(), '{}')]"
        self.session.at_xpath(xpath.format(self.app.title())).click()
        
        self.ensure_application_header()
        self._debug("open_app", "opened")
        

    def create_app(self):
        # xpath = "//*[normalize-space(text()) = 'Add new application']"
        # self.session.at_xpath(xpath).click()
        xpath = "//body/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/h2/button[position()=1]"
        self.session.at_xpath(xpath).click()
        self._debug("create_app", "popup opened")

        self.session.at_css("div.popupContent input").set(self.app.title())
        self._debug("create_app", "filled")
        
        self.session.at_css("div.popupContent select").set("en-US")
        self._debug("create_app", "default_language_set['en-US']")
        
        # xpath = "//*[normalize-space(text()) = 'Prepare Store Listing']"
        # self.session.at_xpath(xpath).click()
        xpath = "//div[@class='gwt-PopupPanel']/div[@class='popupContent']//footer/button[position()=2]"
        self.session.at_xpath(xpath).click()
        
        self.ensure_application_header()
        self._debug("create_app", "created")
        
    
    def remove_languages(self):
        # 'Manage translations' button
        xpath = "//section/div/div/div/div/div/div[3]/button[not(@aria-hidden='true')]"
        if self.session.at_xpath(xpath):
            self.session.at_xpath(xpath).click()
            # 'Remove translations' item
            xpath = "//section/div/div/div/div/div/div[3]/div/ul/li[2]/a"
            self.session.at_xpath(xpath).click()
            buttons = self.session.xpath("//section/div[3]/div[2]/div/div/div/div/button[not(@disabled) and @data-lang-code and @aria-pressed='false']")
            for button in buttons:
                button.click()
            # 'Remove' button
            xpath = "//section/div[3]/div[2]/div/div/div[2]/button[2]"
            self.session.at_xpath(xpath).click()
            self._debug("remove_languages", "old removed")


    def add_languages(self):
        xpath = "//section/div/div/div/div/div/button"
        self.session.at_xpath(xpath).click()
        self.ensure_application_header()
        self._debug("add_languages", "popup_opened")
        new_lang = False
        
        if hasattr(self.app.obj.application, "description-localization"):
            for desc in self.app.obj.application["description-localization"]:
                xpath = "//div[@class='popupContent']//tr/td/div/label/span[contains(text(), ' {}')]"
                xpath = xpath.format(desc.attrib["language"])
                
                if self.session.at_xpath(xpath) != None:
                    new_lang = True
                    self.session.at_xpath(xpath).click()
                    # self._debug("add_languages", desc.attrib["language"])
                
            if not new_lang:
                xpath = "//div[@class='popupContent']//footer/button[last()]"
                self.session.at_xpath(xpath).click()
            else:
                xpath = "//div[@class='popupContent']//footer/button[position()=1]"
                self.session.at_xpath(xpath).click()
        
        self._debug("add_languages", "finished")
        
    def select_language(self, lang):
        xpath = "//button[contains(@data-lang-code, '{}')]"
        xpath = xpath.format(lang)
        button = self.session.at_xpath(xpath)
        if button:
            button.click()
        else:
            # Expand languages list
            xpath = "//section/div[3]/div[2]/div[1]/div/div[1]/div[2]/button"
            self.session.at_xpath(xpath).click()
            # Click on language item in list
            xpath = "//section/div[3]/div[2]/div/div/div/div[2]/div/ul[3]/li/a/span[contains(., ' {}')]"
            xpath = xpath.format(lang)
            #self._debug("select_language", "before click")
            self.session.at_xpath(xpath).click()

    def fill_store_listing(self):
        self._debug("fill_store_listing", "start")
        self.remove_languages()
        self.add_languages()
        self.select_language('en-US')
        self.fill_localization("default")
        
        if hasattr(self.app.obj.application, "description-localization"):
            for desc in self.app.obj.application["description-localization"]:
                self.select_language(desc.attrib["language"])
                self.fill_localization(desc.attrib["language"])
    
    def fill_localization(self, lang):
        inputs = self.session.css("fieldset input")
        textareas = self.session.css("fieldset textarea")
        selects = self.session.css("fieldset select")

        assert len(inputs) == 7
        assert len(textareas) == 3
        assert len(selects) == 3
        fill(inputs, [
            self.app.title(lang),
            self.app.video(),
            self.app.website(),
            self.app.email(),
            self.app.phone(),
            self.app.privacy_policy_link()
        ])
        fill(textareas, [
            self.app.full_description(lang),
            self.app.short_description(lang),
            self.app.recent_changes(lang)
        ])

        if lang == "default":
            fill_element(selects[0], self.app.type())

            #self.session.wait_while(lambda: selects[1].get_bool_attr("disabled"))
            # Find category value
            xpath = "//option[contains(text(), '{}')]"
            xpath = xpath.format(self.app.category())
            option = self.session.at_xpath(xpath)
            fill_element(selects[1], option.value())

            fill_element(selects[2], self.app.rating())
        
            # Upload screenshots
            # Remove old screenshots first
            xpath = "//section/div[3]/div[2]/div[3]/div[2]/div[1]/div/div[2]/div[1]/div[1]/div[1]/div[2]/div"
            old_screenshots = self.session.xpath(xpath)
            self._debug("screenshots", "start")
            for old in old_screenshots:
                if old.at_xpath("div[3]").get_attr("aria-hidden") != "true":
                    old.at_xpath("div[3]/div[2]").click()
            self._debug("screenshots", "old deleted")
            screenshots = self.app.screenshot_paths()
            # Dirty hack :(
            self.upload_file(self.session.xpath(xpath)[-1].at_xpath("div[1]/input"), screenshots[0])

            for screenshot in screenshots:
                for i in xrange(IMAGE_LOAD_ATTEMPTS):
                    if self.upload_image(self.session.xpath(xpath)[-1], screenshot):
                        break

            # Upload app icon
            app_icon_path = self.app.app_icon_path()
            xpath = "//section/div[3]/div[2]/div[3]/div[2]/div[2]/div/div[2]/div/div"
            app_icon_div = self.session.at_xpath(xpath)
            for i in xrange(IMAGE_LOAD_ATTEMPTS):
                if self.upload_image(app_icon_div, app_icon_path):
                    break

            # Upload large promo
            large_promo_path = self.app.large_promo_path()
            if large_promo_path != None:
                xpath = "//section/div[3]/div[2]/div[3]/div[2]/div[2]/div[2]/div[2]"
                large_promo_div = self.session.at_xpath(xpath)
                for i in xrange(IMAGE_LOAD_ATTEMPTS):
                    if self.upload_image(large_promo_div, large_promo_path):
                        break

            # Upload small promo
            small_promo_path = self.app.small_promo_path()
            if small_promo_path != None:
                xpath = "//section/div[3]/div[2]/div[3]/div[2]/div[2]/div[3]/div[2]"
                small_promo_div = self.session.at_xpath(xpath)
                for i in xrange(IMAGE_LOAD_ATTEMPTS):
                    if self.upload_image(small_promo_div, small_promo_path):
                        break

        self.session.at_xpath("//section/h3/button").click()
        self._debug("fill_store_listing['"+lang+"']", "saved")
        assert self.ensure_saved_message()

    def fill_pricing_and_distribution(self):
        xpath = "//sidebar/nav/ol[2]/li[3]/a"
        self.session.at_xpath(xpath).click()
        if self.app.paid():
            xpath = "//section/div[2]/div[2]/fieldset/label/div[2]/div/div/div/button[1]"
            self.session.at_xpath(xpath).click()
            # Select base price
            xpath = "//section/div[2]/div[2]/fieldset/label[2]/div[2]/div/div[1]/div/label"
            label = self.session.at_xpath(xpath)
            base_currency = label.at_xpath("span[1]").text()
            if base_currency == "USD":
                label.at_xpath("input").set(self.app.base_price())
                # Auto-convert prices
                xpath = "//section/div[2]/div[2]/fieldset/label[3]/div[2]/button"
                self.session.at_xpath(xpath).click()
                # Sel manual prices
                local_prices = self.app.local_prices()
                for local_price in local_prices:
                    xpath = "//section/div[2]/div[3]/div/div[1]/div/div/div[3]/div/div[2]/div/div/table/tbody/tr/td[1]/div/label[contains(text(),'{}')]"
                    xpath = xpath.format(local_price[0])
                    country_row = self.session.at_xpath(xpath).at_xpath("../../..")
                    price_input = country_row.at_xpath("td[2]/div/label/input")
                    if price_input:
                        price_input.set(local_price[1])
        else:
            xpath = "//section/div[2]/div[2]/fieldset/label/div[2]/div/div/div/button[2]"
            self.session.at_xpath(xpath).click()
        availability_type = self.app.availability_type()
        if availability_type == "all" or availability_type == "exclude":
            xpath = "//section/div[2]/div[3]/div/div/div/div/div/div[3]/table/thead/tr/th/label/input"
            self.session.at_xpath(xpath).set("false")
            self.session.at_xpath(xpath).set("true")
        countries_list = self.app.availability_countries()
        if availability_type == "include" or availability_type == "exclude":
            for country in countries_list:
                xpath = "//section/div[2]/div[3]/div/div[1]/div/div/div[3]/div/div[2]/div/div/table/tbody/tr/td[1]/div/label[contains(text(),'{}')]"
                xpath = xpath.format(country)
                label = self.session.at_xpath(xpath)
                if label.get_attr("data-country-checkbox") == "blocked":
                    print country, "blocked, skip"
                else:
                    label.at_xpath("input").set("true" if availability_type == "include" else "false")
        if self.app.google_android_content_guidelines():
            xpath = "//section/div[2]/div[5]/fieldset/label[2]/div[2]/div/div/span/input"
            self.session.at_xpath(xpath).click()
        if self.app.us_export_laws():
            xpath = "//section/div[2]/div[5]/fieldset/label[3]/div[2]/div/span/input"
            self.session.at_xpath(xpath).click()
        self.session.at_xpath("//section/h3/button").click()
        self._debug("fill_pricing_and_distribution", "saved")
        assert self.ensure_saved_message()

    def upload_apk(self):
        xpath = "//sidebar/nav/ol[2]/li[1]/a"
        self.session.at_xpath(xpath).click()
        self.ensure_application_header()
        
        # 'Upload new APK to production' button
        xpath = "//section/div/div/div/div/div/div/div/button"
        button = self.session.at_xpath(xpath)
        if not button or not button.is_visible():
            # Button if APK is already exist
            xpath = "//section/div[2]/div/div/div[2]/h3/button"
            button = self.session.at_xpath(xpath)
        button.click()
        self.ensure_application_header()
        
        # 'input' for APK upload
        xpath = "//div[@class='gwt-PopupPanel']/div[@class='popupContent']/div/div/div/input"
        input_file = self.session.at_xpath(xpath)
        apk_list = self.app.apk_paths()
        self.upload_file(input_file, apk_list[0])
        # 'div' with progress bar
        self.session.wait_for(self.apk_loading_check, interval=0.1, timeout=120)
        print "\rUpload APK: done!", " " * 15
        # 'div' with warnings
        xpath = "/html/body/div[6]/div/div/div[1]/div[4]"
        warnings_block = self.session.at_xpath(xpath)
        if warnings_block.get_attr("aria-hidden") != "true":
            print "\nUpload APK:", warnings_block.at_xpath("h4").text()
            for warning in warnings_block.xpath("div/p"):
                print "*", warning.text()
        # 'div' with errors
        xpath = "/html/body/div[6]/div/div/div[1]/div[3]"
        errors_block = self.session.at_xpath(xpath)
        if errors_block.get_attr("aria-hidden") != "true":
            print "\nUploading APK:", errors_block.at_xpath("h4").text()
            for error in errors_block.xpath("div/p"):
                print "*", error.text()
            sys.exit(1)
        # 'Save' button
        xpath = "/html/body/div[6]/div/div/nav/span/div/button[1]"
        save_button = self.session.at_xpath(xpath)
        if save_button and save_button.is_visible():
            save_button.click()
        self._debug("upload_apk", "finished")
    
    def apk_loading_check(self):
        xpath = "/html/body/div[6]/div/div/div[1]/div[2]"
        progress_bar = self.session.at_xpath(xpath)
        xpath = "/html/body/div[6]/div/div/div[1]/div[2]/div[2]/div[1]/span"
        percent = self.session.at_xpath(xpath).text().split()[0]
        print "\rUploading APK: ", percent,
        sys.stdout.flush()
        return progress_bar.get_attr("aria-hidden") == "true"

    def upload_file(self, file_input, file_path):
        file_input.set_attr("style", "position: absolute")
        file_input.set(file_path)

    def upload_image(self, image_div, image_path):
        # Delete old image if needed
        if image_div.at_xpath("div[1]").get_attr("aria-hidden") == "true":
            image_div.at_xpath("div[not(@aria-hidden='true')]/div[2]").click()

        self.upload_file(image_div.at_xpath("div[1]/input"), image_path)
        self.session.wait_for(lambda: image_div.at_xpath("div[2]").get_attr("aria-hidden") == "true", timeout=60)
        if image_div.at_xpath("div[4]").get_attr("aria-hidden") != "true":
            image_div.at_xpath("div[4]/div[2]").click()
            return False
        print "Uploaded:", os.path.basename(image_path)
        return True

    # Helpers
    def _debug(self, action, state):
        print action + " : " + state
        
        if self.debug_dir:
            file_name = "{}-{}-{}.png".format(time.time(), action, state)
            self.session.render(os.path.join(self.debug_dir, file_name))

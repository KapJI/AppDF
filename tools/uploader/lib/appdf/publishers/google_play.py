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
        self.session.set_header("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.69 Safari/537.36")

        if self.debug_dir:
            if not os.path.exists(self.debug_dir):
                os.mkdir(self.debug_dir)

    # Publication process
    def publish(self):
        self.session.visit("https://play.google.com/apps/publish/v2/")
        self._debug("google play", "opened")

        self.login()
        
        #assert bool(self.ensure_all_applications_header())

        # Select All applications menu
        xpath = "//sidebar/nav/ul/li/a/div"
        all_appications_button = self.session.at_xpath(xpath)
        if all_appications_button:
            all_appications_button.click()
        else:
            print "Login error"
            sys.exit(1)
        
        if self.ensure_application_listed():
            self.open_app()
            self.remove_languages()
        else:
            self.create_app()
        
        self.add_languages()

        self.fill_store_listing()
        self.load_apk()

    # Checks
    def ensure_all_applications_header(self):
        xpath = "//h2[normalize-space(text()) = 'All applications']"
        # TODO All applications == VSE PRILOZHENIYA
        return self._ensure(xpath)

    def ensure_application_listed(self):
        xpath = "//section/div/table/tbody/tr/td/div/a/span[contains(text(), '{}')]"
        return self._ensure(xpath.format(self.app.title()))

    def ensure_application_header(self):
        xpath = "//h2/span[contains(text(), '{}')]".format(self.app.title())
        return self._ensure(xpath)

    def ensure_store_listing_header(self):
        xpath = "//h3[contains(text(), 'Store Listing')]"
        # TODO Store Listing == DANNIE DLY GOOGLE PLAY
        return self._ensure(xpath)

    def ensure_saved_message(self):
        #xpath = "//*[normalize-space(text()) = 'Saved']"
        # TODO Saved == Sohraneno
        xpath = "//div[@data-notification-type='INFO' and @aria-hidden='false']"
        return self._ensure(xpath)

    def ensure_add_language_header(self):
        xpath = "//"
        return self._ensure(xpath)
    
    def _ensure(self, xpath):
        return self.session.at_xpath(xpath, timeout=5)

    # Actions

    def login(self):
        login_url = "https://accounts.google.com/ServiceLogin"

        if self.session.url().startswith(login_url):
            email_field = self.session.at_css("#Email")
            password_field = self.session.at_css("#Passwd")
            email_field.set(self.username)
            password_field.set(self.password)
            self._debug("login", "filled")
            
            email_field.form().submit()
            self.ensure_all_applications_header()
            self._debug("login", "submited")

    def open_app(self):
        xpath = "//section/div/table/tbody/tr/td/div/a/span[contains(text(), '{}')]"
        self.session.at_xpath(xpath.format(self.app.title())).click()
        
        # TODO select default language
        
        self.ensure_application_header()
        self._debug("open_app", "opened")
        

    def create_app(self):
        # xpath = "//*[normalize-space(text()) = 'Add new application']"
        # self.session.at_xpath(xpath).click()
        xpath = "//body/div/div/div/div/div/div/div/div/div/div/div/div/div/div/div/h2/button[position()=1]"
        self.session.at_xpath(xpath).click()
        self._debug("create_app", "popup_opened")

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
        xpath = "//section/div/div/div/div/div/div[3]/button[@aria-hidden='false']"
        if self.session.at_xpath(xpath):
            self.session.at_xpath(xpath).click()
            # 'Remove translations' item
            xpath = "//section/div/div/div/div/div/div[3]/div/ul/li[2]/a"
            self.session.at_xpath(xpath).click()
            buttons = self.session.xpath("//section/div[3]/div[2]/div/div/div/div/button[not(@disabled) and @data-lang-code and @aria-pressed='false']")
            for button in buttons:
                button.click()
            self._debug("remove_languages", "all selected")
            # 'Remove' button
            xpath = "//section/div[3]/div[2]/div/div/div[2]/button[2]"
            self.session.at_xpath(xpath).click()


    def add_languages(self):
        xpath = "//section/div/div/div/div/div/button"
        self.session.at_xpath(xpath).click()
        self.ensure_application_header()
        self._debug("add_languages", "popup_opened")
        new_local = 0
        
        if hasattr(self.app.obj.application, "description-localization"):
            for desc in self.app.obj.application["description-localization"]:
                xpath = "//div[@class='popupContent']//tr/td/div/label/span[contains(text(), ' {}')]"
                xpath = xpath.format(desc.attrib["language"])
                
                if self.session.at_xpath(xpath) != None:
                    new_local = 1
                    self.session.at_xpath(xpath).click()
                    # self._debug("add_languages", desc.attrib["language"])
                
            if new_local == 0:
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
        self.select_language('en-US')
        self.fill_localization("default")
        
        if hasattr(self.app.obj.application, "description-localization"):
            for desc in self.app.obj.application["description-localization"]:
                self.select_language(desc.attrib["language"])
                self.fill_localization(desc.attrib["language"])
    
    def fill_localization(self, local):
        inputs = self.session.css("fieldset input")
        textareas = self.session.css("fieldset textarea")
        selects = self.session.css("fieldset select")

        assert len(inputs) == 7
        assert len(textareas) == 3
        assert len(selects) == 3
        fill(inputs, [
            self.app.title(local),
            self.app.video(),
            self.app.website(),
            self.app.email(),
            self.app.phone(),
            self.app.privacy_policy_link()
        ])
        features = "\n".join(["* " + feature for feature in self.app.features(local)])
        full_description = "\n".join([self.app.full_description(local), features.encode("utf-8")])
        fill(textareas, [
            full_description,
            self.app.short_description(local),
            self.app.recent_changes(local)
        ])

        if local == "default":
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
                if old.at_xpath("div[3]").get_attr("aria-hidden") == "false":
                    old.at_xpath("div[3]/div[2]").click()
            self._debug("screenshots", "old deleted")
            screenshots = self.app.screenshot_paths()
            # Dirty hack :(
            self.upload_file(self.session.xpath(xpath)[-1].at_xpath("div[1]/input"), screenshots[0])

            for screenshot in screenshots:
                print screenshot
                for i in xrange(IMAGE_LOAD_ATTEMPTS):
                    if self.upload_image(self.session.xpath(xpath)[-1], screenshot):
                        break
            self._debug("screenshots", "loaded")

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
        self._debug("fill_store_listing['"+local+"']", "saved")
        assert self.ensure_saved_message()

    def load_apk(self):
        xpath = "//sidebar/nav/ol[@aria-hidden='false']/li/a"
        self.session.at_xpath(xpath).click()
        self.ensure_application_header()
        self._debug("load_apk", "select_apk_folder")
        
        xpath = "//section/div/div/div/div/div/div/div/button"
        button = self.session.at_xpath(xpath)
        if not button or not button.is_visible():
            xpath = "//section/div[2]/div/div/div[2]/h3/button"
            button = self.session.at_xpath(xpath)
        button.click()
        self.ensure_application_header()
        
        xpath = "//div[@class='gwt-PopupPanel']/div[@class='popupContent']/div/div/div/input"
        input_file = self.session.at_xpath(xpath)
        apk_list = self.app.apk_paths()
        self.upload_file(input_file, apk_list[0])
        xpath = "/html/body/div[6]/div/div/div[1]/div[2]"
        progress_bar = self.session.at_xpath(xpath)
        self.session.wait_for(lambda: progress_bar.get_attr("aria-hidden") == "true", timeout=120)
        xpath = "/html/body/div[6]/div/div/nav/span/div/button[1]"
        save_button = self.session.at_xpath(xpath)
        if save_button and save_button.is_visible():
            print "Click Save APK"
            save_button.click()
        time.sleep(1)
        self._debug("upload_apk", "loaded")
    
    def upload_file(self, file_input, file_path):
        file_input.set_attr("style", "position: absolute")
        file_input.set(file_path)

    def upload_image(self, image_div, image_path):
        # Delete old image if needed
        if image_div.at_xpath("div[1]").get_attr("aria-hidden") == "true":
            image_div.at_xpath("div[@aria-hidden='false']/div[2]").click()

        self.upload_file(image_div.at_xpath("div[1]/input"), image_path)
        self.session.wait_for(lambda: image_div.at_xpath("div[2]").get_attr("aria-hidden") == "true")
        if image_div.at_xpath("div[4]").get_attr("aria-hidden") == "false":
            image_div.at_xpath("div[4]/div[2]").click()
            return False
        return True

    # Helpers
    def _debug(self, action, state):
        print action + " : " + state
        
        if self.debug_dir:
            file_name = "{}-{}-{}.png".format(time.time(), action, state)
            self.session.render(os.path.join(self.debug_dir, file_name))

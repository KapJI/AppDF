# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import json
import webkit_server


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


class Amazon(object):
    def __init__(self, app, username, password, debug_dir=None):
        self.app = app
        self.username = username
        self.password = password
        self.debug_dir = debug_dir

        self.session = webkit_server.Client()

        if self.debug_dir:
            if not os.path.exists(self.debug_dir):
                os.mkdir(self.debug_dir)

    def publish(self):
        self.open_console()
        self.login()
        if self.session.at_css("#ap_signin_existing_radio"):
            print "Login error"
            sys.exit(1)
        
        if self.ensure_application_listed():
            self.open_application()
        else:
            self.create_application()
        self.fill_general_information()
        self.fill_availability()
        self.fill_description()
        self.fill_content_rating()
        self.fill_images_multimedia()
        self.fill_binary_files()
            
    
    # Actions
    def open_console(self):
        self.session.visit("https://developer.amazon.com/welcome.html")
        self._debug("developer_console", "opened")

    def login(self):
        xpath = "//a[@id=\"header_login_link\"]"
        self.session.at_xpath(xpath).click()
        
        email_field = self.session.at_css("#ap_email")
        # radio_button
        self.session.at_css("#ap_signin_existing_radio").click()
        password_field = self.session.at_css("#ap_password")
        submit_button = self.session.at_css("#signInSubmit-input")

        email_field.set(self.username)
        password_field.set(self.password)
        
        email_field.form().submit()
        self._debug("login", "submited")
    
    def open_application(self):
        xpath = "//span[@class=\"itemTitle\" and contains(text(), '{}')]"
        self._ensure(xpath.format(self.app.title())).click()
        self._debug("open_application", "finished")
        
    def create_application(self):
        xpath = "//a[@id=\"add_new_app_link\"]"
        self._ensure(xpath).click()
        self._debug("create_application", "finished")
        
    def fill_general_information(self):
        xpath = "//a[@id=\"header_nav_general_information_a\"]"
        if self.session.at_xpath(xpath):
            self.session.at_xpath(xpath).click();
            
        xpath = "//a[@id=\"edit_button\"]"
        if self.session.at_xpath(xpath):
            self.session.at_xpath(xpath).click();
        
        if self.session.at_xpath("//input[@id=\"same\" and @checked]"):
            self.session.at_xpath("//input[@id=\"same\" and @checked]").click()
        
        fill([
            self.session.at_xpath("//input[@id=\"title\"]"),
            self.session.at_xpath("//input[@id=\"email\"]"),
            self.session.at_xpath("//input[@id=\"phone\"]"),
            self.session.at_xpath("//input[@id=\"website\"]"),
            self.session.at_xpath("//input[@id=\"privacyPolicyUrl\"]")
        ], [
            self.app.title("default"),
            self.app.email(),
            self.app.phone(),
            self.app.website(),
            self.app.privacy_policy_link()
        ])
        
        # Category selection
        xpath = "//select[@id=\"parentCategoryList\"]/option[contains(text(), \"{}\")]"
        xpath = xpath.format(self.app.category())
        category_value = self.session.at_xpath(xpath).value()
        fill([
            self.session.at_xpath("//select[@id=\"parentCategoryList\"]"),
            self.session.at_xpath("//input[@id=\"selectedCategory\"]")
        ], [
            category_value,
            category_value
        ])
        
        # Subcategory selection
        if self.app.subcategory() != "":
            #print 'Subcategory:', self.app.subcategory()
            xpath = "//select[@id=\"childCategoryList\"]/option[contains(text(), \"{}\")]"
            xpath = xpath.format(self.app.subcategory())
            subcategory_value = self.session.at_xpath(xpath).get_attr("value")
            if self.session.at_xpath(xpath):
                fill([
                    self.session.at_xpath("//select[@id=\"childCategoryList\"]"),
                    self.session.at_xpath("//input[@id=\"selectedCategory\"]")
                ], [
                    subcategory_value,
                    subcategory_value
                ])
            
        xpath = "//input[@id=\"submit_button\"]"
        self.session.at_xpath(xpath).click();
        self._debug("general_info", "saved")
        self.error_check()
        
    def fill_availability(self):
        xpath = "//a[@id=\"header_nav_availability_pricing_a\"]"
        if self.session.at_xpath(xpath):
            self._ensure(xpath).click();
        
        xpath = "//a[@id=\"edit_button\"]"
        if self.session.at_xpath(xpath):
            self._ensure(xpath).click();
        
        # Countries
        if self.app.availability_type() == "include":
            self.session.at_xpath("//input[@id=\"availableWorldWide2\"]").click()
            
            # Remove selection
            for selection in ["AF", "AN", "AS", "EU", "NA", "OC", "SA"]:
                length = len(str(self.session.at_xpath("//span[@id=\"selected-countries\"]").text()))
                self.session.at_xpath("//div[@id=\"" + selection + "\"]/label[1]/input").click()
                if length < len(str(self.session.at_xpath("//span[@id=\"selected-countries\"]").text())):
                    self.session.at_xpath("//div[@id=\"" + selection + "\"]/label[1]/input").click()
                
            # Only listed
            for country in self.app.availability_countries():
                country = country.encode("utf-8")
                if self.session.at_xpath("//input[@id=\"" + country + "\"]"):
                    self.session.at_xpath("//input[@id=\"" + country + "\"]").click()
            
        elif self.app.availability_type() == "exclude":
            self.session.at_xpath("//input[@id=\"availableWorldWide2\"]").click()
            
            # Set selection
            for selection in ["AF", "AN", "AS", "EU", "NA", "OC", "SA"]:
                length = len(str(self.session.at_xpath("//span[@id=\"selected-countries\"]").text()))
                self.session.at_xpath("//div[@id=\"" + selection + "\"]/label[1]/input").click()
                if length > len(str(self.session.at_xpath("//span[@id=\"selected-countries\"]").text())):
                    self.session.at_xpath("//div[@id=\"" + selection + "\"]/label[1]/input").click()
            
            # All except
            for country in self.app.availability_countries():
                country = country.encode("utf-8")
                if self.session.at_xpath("//input[@id=\"" + country + "\"]"):
                    self.session.at_xpath("//input[@id=\"" + country + "\"]").click()
            
        else:
            self.session.at_xpath("//input[@id=\"availableWorldWide1\"]").click()
            
        # Prices
        if self.app.paid():
            self.session.at_xpath("//input[@id=\"charging-yes\"]").click()
            fill([
                self.session.at_xpath("//select[@id=\"base_currency\"]"),
                self.session.at_xpath("//input[@id=\"price\"]")
            ],[
                "USD", #base currency
                self.app.base_price()
            ])
            
            self.session.at_xpath("//input[@id=\"pricing_custom\"]").click()
            
            currency = self.app.currency()
            for local_price in self.app.local_prices():
                country = local_price[0]
                price = local_price[1]
                if country in currency:
                    fill_element(
                        self.session.at_xpath("//input[@id=\"" + currency[country] + "_" + country + "\"]"),
                        price
                    )
        else:
            self.session.at_xpath("//input[@id=\"charging-no-free-app\"]").click()
        
        # Period
        if self.app.period_since() != None:
            fill([
                self.session.at_xpath("//input[@id=\"availabilityDate\"]")
            ],[
                self.app.period_since()
            ])
        
        # Free app of day
        fill([
            self.session.at_xpath("//input[@id=\"fad\"]")
        ], [
            self.app.free_app_of_day()
        ])
        
        xpath = "//input[@id=\"submit_button\"]"
        self.session.at_xpath(xpath).click();
        self._debug("fill_availability", "saved")
        self.error_check()
        
    def fill_description(self):
        xpath = "//a[@id=\"header_nav_description_a\"]"
        if self.session.at_xpath(xpath):
            self._ensure(xpath).click();
        
        self.form_description("default")
        
        if hasattr(self.app.obj.application, "description-localization"):
            language_json = self.app.language()
            for desc in self.app.obj.application["description-localization"]:
                language = desc.attrib["language"]
                if language in language_json:
                    xpath = "//ul[@id=\"collectable_nav_list\"]/li/a[contains(text(), \"{}\")]"
                    xpath = xpath.format(language_json[language])
                    if self.session.at_xpath(xpath):
                        self.session.at_xpath(xpath).click()
                        self.form_description(language)
                    else:
                        xpath = "//ul[@id=\"collectable_nav_list\"]/li[last()]/a"
                        self.session.at_xpath(xpath).click()
                        self.form_description(language, language_json[language])
        
    def form_description(self, lang="default", locale_label=""):
        xpath = "//a[@id=\"edit_button\"]"
        if self.session.at_xpath(xpath):
            self._ensure(xpath).click();
        elif locale_label != "":
            xpath = "//select[@id=\"locale\"]/option[contains(text(), \"{}\")]"
            xpath = xpath.format(locale_label)
            fill([
                self.session.at_xpath("//select[@id=\"locale\"]")
            ], [
                self.session.at_xpath(xpath).value()
            ])
        
        fill([
            self.session.at_xpath("//textarea[@id=\"dpShortDescription\"]"),
            self.session.at_xpath("//textarea[@id=\"publisherDescription\"]"),
            self.session.at_xpath("//textarea[@id=\"dpMarketingBulletsStr\"]"),
            self.session.at_xpath("//textarea[@id=\"keywordsString\"]")
        ], [
            self.app.short_description(lang),
            self.app.full_description(lang),
            '\n'.join(self.app.features(lang)),
            self.app.keywords(lang)
        ])
        self._debug("description", "fill_"+lang)
        
        xpath = "//input[@id=\"submit_button\"]"
        self.session.at_xpath(xpath).click();
        self._debug("description", "store_"+lang)
        self.error_check()
        
    def fill_images_multimedia(self):
        xpath = "//a[@id=\"header_nav_multimedia_a\"]"
        if self.session.at_xpath(xpath):
            self._ensure(xpath).click();
        
        xpath = "//a[@id=\"edit_button\"]"
        if self.session.at_xpath(xpath):
            self._ensure(xpath).click();
        self._debug("images_multimedia", "opened")

        # Small application icon
        small_icon_path = self.app.small_app_icon_path()
        xpath = "//*[@id='itemsection_multimedia']/div/fieldset/table/tbody/tr[1]/td[2]/div"
        self.delete_file(self.session.at_xpath(xpath))
        self.upload_file(self.session.at_xpath(xpath + "/div[@class='asset']"), small_icon_path)

        # Application icon
        app_icon_path = self.app.app_icon_path()
        xpath = "//*[@id='itemsection_multimedia']/div/fieldset/table/tbody/tr[2]/td[2]/div"
        self.delete_file(self.session.at_xpath(xpath))
        self.upload_file(self.session.at_xpath(xpath + "/div[@class='asset']"), app_icon_path)

        # Delete old screenshot
        xpath = "//*[@id='itemsection_multimedia']/div/fieldset/table/tbody/tr[3]/td[2]"
        while self.delete_file(self.session.at_xpath(xpath)):
            pass

        self._debug("old_screenshots", "deleted")
        screenshots = self.app.screenshot_paths()
        for screenshot in screenshots:
            self.upload_file(self.session.at_xpath(xpath + "/div[@class='asset']"), screenshot)

        large_promo_path = self.app.large_promo_path()
        if large_promo_path:
            xpath = "//*[@id='itemsection_multimedia']/div/fieldset/table/tbody/tr[4]/td[2]/div"
            self.delete_file(self.session.at_xpath(xpath))
            self.upload_file(self.session.at_xpath(xpath + "/div[@class='asset']"), large_promo_path)

        xpath = "//input[@id=\"submit_button\"]"
        self.session.at_xpath(xpath).click();
        self._debug("images_multimedia", "saved")
        self.error_check()
        
    def fill_content_rating(self):
        xpath = "//a[@id=\"header_nav_rating_a\"]"
        if self.session.at_xpath(xpath):
            self._ensure(xpath).click();
        
        xpath = "//a[@id=\"edit_button\"]"
        if self.session.at_xpath(xpath):
            self._ensure(xpath).click();
        
        content_desc = self.app.content_desc()
        
        xpath = "//input[@id=\"maturityratingcategory.alcohol_tobacco_or_drug_use_or_references_" + content_desc[0] + "\"]"
        self.session.at_xpath(xpath).click()
        xpath = "//input[@id=\"maturityratingcategory.cartoon_or_fantasy_violence_" + content_desc[1] + "\"]"
        self.session.at_xpath(xpath).click()
        xpath = "//input[@id=\"maturityratingcategory.cultural_or_religious_intolerance_" + content_desc[2] + "\"]"
        self.session.at_xpath(xpath).click()
        xpath = "//input[@id=\"maturityratingcategory.nudity_" + content_desc[3] + "\"]"
        self.session.at_xpath(xpath).click()
        xpath = "//input[@id=\"maturityratingcategory.profanity_or_crude_humor_" + content_desc[4] + "\"]"
        self.session.at_xpath(xpath).click()
        xpath = "//input[@id=\"maturityratingcategory.realistic_violence_" + content_desc[5] + "\"]"
        self.session.at_xpath(xpath).click()
        xpath = "//input[@id=\"maturityratingcategory.sexual_and_suggestive_content_" + content_desc[6] + "\"]"
        self.session.at_xpath(xpath).click()
        
        fill([
            self.session.at_xpath("//input[@id=\"maturityratingcategory.account_creation\"]"),
            self.session.at_xpath("//input[@id=\"maturityratingcategory.advertisements\"]"),
            self.session.at_xpath("//input[@id=\"maturityratingcategory.gambling\"]"),
            self.session.at_xpath("//input[@id=\"maturityratingcategory.location_detection\"]"),
            self.session.at_xpath("//input[@id=\"maturityratingcategory.user_generated_content_or_user_to_user_communication\"]")
        ], 
            self.app.include_content()
        )
        
        xpath = "//input[@id=\"submit_button\"]"
        self.session.at_xpath(xpath).click();
        self._debug("content_rating", "saved")
        self.error_check()
        
    def fill_binary_files(self):
        xpath = "//a[@id=\"header_nav_binary_a\"]"
        if self.session.at_xpath(xpath):
            self._ensure(xpath).click();
        
        xpath = "//a[@id=\"edit_button\"]"
        if self.session.at_xpath(xpath):
            self._ensure(xpath).click();
        self._debug("binary_files", "opened")
        
        # Upload APK
        apk_path = self.app.apk_paths()[0]
        xpath = "//*[@id='itemsection_binary']/div/fieldset/table/tbody/tr[4]/td[2]/div"
        self.delete_file(self.session.at_xpath(xpath))
        self.upload_file(self.session.at_xpath(xpath + "/div[@class='asset']"), apk_path)

        # Apply Amazon DRM
        if self.app.apply_amazon_drm():
            self.session.at_xpath("//*[@id='applyAmazonDRM1']").click()
        else:
            self.session.at_xpath("//*[@id='applyAmazonDRM2']").click()

        # Language support
        # Uncheck all
        lang_checkboxes = self.session.xpath("//*[@id='supportedLanguages']/label/input[@type='checkbox']")
        for checkbox in lang_checkboxes:
            checkbox.set("false")
        self.session.at_xpath("//*[@id='English']").set("true")
        # TODO: implement this
        # if hasattr(self.app.obj.application, "description-localization"):
        #     language_json = self.app.language()
        #     for desc in self.app.obj.application["description-localization"]:
        #         language = desc.attrib["language"]
        #         if language in language_json:
        
        # Device support
        self.session.at_xpath("//*[@id='selectedCollectableMetaData.allNonAmazonDevicesSupported1']").set("true")
        self.session.at_xpath("//*[@id='MGVY776RM7ZQ0']").set("true" if self.app.kindle_fire_first_generation() else "false")
        self.session.at_xpath("//*[@id='M9C112PAOVM7I']").set("true" if self.app.kindle_fire() else "false")
        self.session.at_xpath("//*[@id='M3U9QPRY5HG6KY']").set("true" if self.app.kindle_fire_hd() else "false")
        self.session.at_xpath("//*[@id='M29F7OKPA4P35O']").set("true" if self.app.kindle_fire_hd_89() else "false")

        # Export Compliance
        self.session.at_xpath("//*[@id='isExportCompliance']").set("true" if self.app.us_export_laws() else "false")

        # Binary alias
        binary_alias = self.app.binary_alias().text.replace(" ", "_")
        self.session.at_xpath("//*[@id='nickName']").set(binary_alias)

        # Testing instructions
        self.session.at_xpath("//*[@id='instructions']").set(self.app.testing_instructions())

        xpath = "//input[@id=\"submit_button\"]"
        self.session.at_xpath(xpath).click();
        self._debug("binary_files", "saved")
        self.error_check()
    
    def delete_file(self, file_div):
        delete_button = file_div.at_xpath("div/div/a[contains(@class, 'remove')]")
        if delete_button:
            delete_button.click()
            self.session.at_xpath("//input[@id='floatingconfirm-ok']").click()
            return True
        return False

    def upload_file(self, file_div, file_path):
        file_div.set_attr("class", "")
        file_div.at_xpath("div/input").set(file_path)
        print "Uploaded:", os.path.basename(file_path)

    # Checks
    def ensure_application_listed(self):
        xpath = "//span[@class=\"itemTitle\" and contains(text(), '{}')]"
        return self._ensure(xpath.format(self.app.title()))
    
    def _ensure(self, xpath):
        return self.session.at_xpath(xpath, timeout=5)
        
    def error_check(self):
        if self.session.at_xpath("//p[@class=\"error\"]"):
            #print self.session.at_xpath("//p[@class=\"error\"]").text()
            #print self.session.at_xpath("//span[@class=\"error-row\"]/@id").value() + \
            #    ":" + self.session.at_xpath("//span[@class=\"error-row\"]").text()
            self._debug("error", self.session.at_xpath("//span[@class=\"error-row\"]").text())
            sys.exit(1)
    
    # Helpers
    def _debug(self, action, state):
        print action + " : " + state
        
        if self.debug_dir:
            file_name = "{}-{}-{}.png".format(time.time(), action, state)
            self.session.render(os.path.join(self.debug_dir, file_name))
        

import os
import zipfile
import json
import lxml.etree
import lxml.objectify
import re

import sys

def silent_normalize(f):
    def decorate(self, local="default"):
        try:
            if local=="default":
                node = f(self)
            else:
                node = f(self, local)
            return node.text.encode("utf-8")
        except AttributeError:
            return None

    return decorate


class AppDF(object):
    def __init__(self, file_path):
        self.file_path = file_path
        self.archive = None

    def parse(self):
        archive = zipfile.ZipFile(self.file_path, "r")
        if archive.testzip():
            raise RuntimeError("AppDF file `{}' is broken".format(file))

        if "description.xml" not in archive.namelist():
            raise RuntimeError("Invalid AppDF file `{}'".format(file))

        self.archive = archive
        self.xml = archive.read("description.xml")
        self.obj = lxml.objectify.fromstring(self.xml)
    
    def validate(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        xsd_file = os.path.join(current_dir, "..", "..", "..", "spec",
                                "appdf-description.xsd")
        schema = lxml.etree.XMLSchema(lxml.etree.parse(xsd_file))
        schema.assertValid(lxml.etree.fromstring(self.xml))

    @silent_normalize
    def title(self, local="default"):
        if local == "default":
            return self.obj.application.description.texts.title #required tag
        elif hasattr(self.obj.application, "description-localization"): #optional tags
            for desc in self.obj.application["description-localization"]:
                if desc.attrib["language"] == local:
                    if hasattr(desc, "texts") and hasattr(desc.texts, "title"):  #optional tags
                        return desc.texts.title
                    else:
                        return ""
        else:
            return ""
            
    def video(self): #optional tags
        if hasattr(self.obj.application.description, "videos") and hasattr(self.obj.application.description.videos, "youtube-video") and self.obj.application.description.videos["youtube-video"]:
            video_id = self.obj.application.description.videos["youtube-video"]
            url = "http://www.youtube.com/watch?v={}".format(video_id)
            return url
        else:
            return ""

    @silent_normalize
    def website(self): #required tags
        site = str(self.obj.application["customer-support"].website)
        if re.search("http", site) == None:
            site = "http://" + site
        return site

    @silent_normalize
    def email(self): #required tags
        return self.obj.application["customer-support"].email

    @silent_normalize
    def phone(self): #required tags
        return self.obj.application["customer-support"].phone

    @silent_normalize
    def privacy_policy(self): #optional tag
        if hasattr(self.obj.application.description.texts, "privacy-policy"):
            return self.obj.application.description.texts["privacy-policy"]
        else:
            return ""

    def privacy_policy_link(self): #optional tag
        if hasattr(self.obj.application.description.texts, "privacy-policy"):
            return self.obj.application.description.texts["privacy-policy"].attrib["href"]
        else:
            return ""

    @silent_normalize
    def full_description(self, local="default"):
        try:
            if local=="default": #required tag
                return self.obj.application.description.texts["full-description"]
            elif hasattr(self.obj.application, "description-localization"): #optional tag
                for desc in self.obj.application["description-localization"]:
                    if desc.attrib["language"]==local:
                        if hasattr(desc, "texts") and hasattr(desc.texts, "full-description"):
                            return desc.texts["full-description"]
                        else:
                            return ""
        except AttributeError:
            return ""

    @silent_normalize
    def short_description(self, local="default"):
        try:
            if local=="default": #required tag
                return self.obj.application.description.texts["short-description"]
            elif hasattr(self.obj.application, "description-localization"): #optional tag
                for desc in self.obj.application["description-localization"]:
                    if desc.attrib["language"]==local:
                        if hasattr(desc, "texts") and hasattr(desc.texts, "short-description"):
                            return desc.texts["short-description"]
                        else:
                            return ""
        except AttributeError:
            return ""

    def features(self, local="default"):
        result = []
        if local=="default":
            for feature in self.obj.application.description.texts.features.feature:
                result.append(unicode(feature))
        else:
            for desc in self.obj.application["description-localization"]:
                if desc.attrib["language"]==local:
                    if hasattr(desc, "texts") and hasattr(desc.texts, "features") and hasattr(desc.texts.features, "feature"):
                        for feature in desc.texts.features.feature:
                            result.append(unicode(feature))
                    else:
                        break
        return result
    
    @silent_normalize
    def recent_changes(self, local="default"):
        if local=="default": #optional tag
            if hasattr(self.obj.application.description.texts, "recent-changes"):
                return self.obj.application.description.texts["recent-changes"]
            else:
                return ""
        elif hasattr(self.obj.application, "description-localization"): #optional tag
            for desc in self.obj.application["description-localization"]:
                if desc.attrib["language"]==local:
                    if hasattr(desc, "texts") and hasattr(desc.texts, "recent-changes"):
                        return desc.texts["recent-changes"]
                    else:
                        return ""

    @silent_normalize
    def type(self): #required tag
        return self.obj.application.categorization.type

    @silent_normalize
    def category(self): #required tag
        return self.obj.application.categorization.category
        
    @silent_normalize
    def subcategory(self): #optional tag
        if hasattr(self.obj.application.categorization, "subcategory"):
            return self.obj.application.categorization.subcategory
        else:
            return ""

    @silent_normalize
    def rating(self): #required tag
        return self.obj.application["content-description"]["content-rating"]
    
    def paid(self):
        return self.obj.application.price.attrib["free"] != "yes"
    
    def base_price(self):
        return self.obj.application.price["base-price"]
    
    def local_prices(self):
        return self._local_prices("countries.json")

    def _local_prices(self, filename):
        result = []
        if hasattr(self.obj.application.price, "local-price"):
            current_dir = os.path.dirname(os.path.realpath(__file__))
            countries_file = os.path.join(current_dir, "..", "..", "..", "spec", filename)
            
            with open(countries_file, "r") as fp:
                countries_json = json.load(fp)
                for local_price in self.obj.application.price["local-price"]:
                    result.append([countries_json[local_price.attrib["country"]], str(local_price)])
        return result
    
    def availability_type(self):
        result = []
        if hasattr(self.obj.application, "availability") and hasattr(self.obj.application.availability, "countries"):
            country = self.obj.application.availability.countries
            if country.attrib["only-listed"] == "yes":
                return "include"
            else:
                return "exclude"
        else: 
            return "all"
            
    def availability_countries(self):
        return self._availability_countries("countries.json")

    def _availability_countries(self, filename):
        result = []
        if hasattr(self.obj.application, "availability") and hasattr(self.obj.application.availability, "countries"):
            current_dir = os.path.dirname(os.path.realpath(__file__))
            countries_file = os.path.join(current_dir, "..", "..", "..", "spec", filename)
            
            with open(countries_file, "r") as fp:
                countries_json = json.load(fp)
                country = self.obj.application.availability.countries
                if country.attrib["only-listed"] == "yes":
                    for include in country.include:
                        if include in countries_json:
                            result.append(countries_json[include])
                else:
                    for exclude in country.exclude:
                        if exclude in countries_json:
                            result.append(countries_json[exclude])
        return result

    def period_since(self):
        if hasattr(self.obj.application, "availability") and hasattr(self.obj.application.availability, "period"):
            if hasattr(self.obj.application.availability.period, "since"):
                since = self.obj.application.availability.period.since
                return since.attrib["month"] + "/" + since.attrib["day"] + "/" + since.attrib["year"][2:4]
        return None
        
    def period_until(self):
        if hasattr(self.obj.application, "availability") and hasattr(self.obj.application.availability, "period"):
            if hasattr(self.obj.application.availability.period, "until"):
                until = self.obj.application.availability.period.until
                return until.attrib["month"] + "/" + until.attrib["day"] + "/" + until.attrib["year"][2:4]
        return None
        
    @silent_normalize
    def keywords(self, local="default"):
        if local=="default": #optional tag
            if hasattr(self.obj.application.description.texts, "keywords"):
                return self.obj.application.description.texts["keywords"]
            else:
                return ""
        elif hasattr(self.obj.application, "description-localization"): #optional tag
            for desc in self.obj.application["description-localization"]:
                if desc.attrib["language"]==local:
                    if hasattr(desc, "texts") and hasattr(desc.texts, "keywords"):
                        return desc.texts["keywords"]
                    else:
                        return ""

    def _get_path_and_extract(self, filename):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        tmp_dir = os.path.join(current_dir, "..", "..", "..", "tmp")
        self.archive.extract(filename, tmp_dir)
        return os.path.join(tmp_dir, str(filename))

    def apk_paths(self):
        result = []
        apk_files = self.obj.application["apk-files"]
        for apk_file in apk_files["apk-file"]:
            result.append(self._get_path_and_extract(apk_file))
        return result

    def app_icon_path(self):
        app_icon_file = self.obj.application.description.images["app-icon"]
        return self._get_path_and_extract(app_icon_file)

    def large_promo_path(self):
        if not hasattr(self.obj.application.description.images, "large-promo"):
            return None
        large_promo_file = self.obj.application.description.images["large-promo"]
        return self._get_path_and_extract(large_promo_file)

    def small_promo_path(self):
        if not hasattr(self.obj.application.description.images, "small-promo"):
            return None
        small_promo_file = self.obj.application.description.images["small-promo"]
        return self._get_path_and_extract(small_promo_file)

    def screenshot_paths(self):
        """ Return paths to screenshots in filesystem with best resolution """
        indexes = dict()
        screenshots = self.obj.application.description.images.screenshots
        for screenshot in screenshots.screenshot:
            index = screenshot.attrib["index"]
            if (index in indexes) and (int(screenshot.attrib["width"]) > int(indexes[index].attrib["width"])) or not index in indexes:
                indexes[index] = screenshot
        result = []
        for key, value in sorted(indexes.items()):
            result.append(self._get_path_and_extract(value))
        return result


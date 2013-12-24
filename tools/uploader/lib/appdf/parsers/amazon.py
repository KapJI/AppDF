from __future__ import absolute_import

import os
import json
import re
import image_resizer
from appdf.parsers import AppDF


class Amazon(AppDF):
    def type(self):
        return super(Amazon, self).type().upper()

    def category(self):
        type = super(Amazon, self).type()
        category = super(Amazon, self).category()
        subcategory = super(Amazon, self).subcategory()
        
        current_dir = os.path.dirname(os.path.realpath(__file__))
        categories_file = os.path.join(current_dir, "..", "..", "..", "spec",
                                       "store_categories.json")
        
        with open(categories_file, "r") as fp:
            categories = json.load(fp)
            if subcategory == None:
                amazon_category = self._replace(categories[type][category][""]["amazon"])
            else:
                amazon_category = self._replace(categories[type][category][subcategory]["amazon"])
                
            return amazon_category.split("/")[0]

    def subcategory(self):
        type = super(Amazon, self).type()
        category = super(Amazon, self).category()
        subcategory = super(Amazon, self).subcategory()
        
        current_dir = os.path.dirname(os.path.realpath(__file__))
        categories_file = os.path.join(current_dir, "..", "..", "..", "spec",
                                       "store_categories.json")
        
        amazon_category = ""
        with open(categories_file, "r") as fp:
            categories = json.load(fp)
            if subcategory == None:
                amazon_category = self._replace(categories[type][category][""]["amazon"])
            else:
                amazon_category = self._replace(categories[type][category][subcategory]["amazon"])
            
        return amazon_category.split("/")[1] if len(amazon_category.split("/")) == 2 else ""
    
    def _replace(self, category):
        category = re.sub("(\s*/\s*)", "/", category)
        category = re.sub("^(\s*)", "", category)
        category = re.sub("(\s*)$", "", category)
        return category
    
    def language(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        languages_file = os.path.join(current_dir, "..", "..", "..", "spec", "amazon_language.json")
        with open(languages_file, "r") as fp:
            return json.load(fp)
    
    def currency(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        currency_file = os.path.join(current_dir, "..", "..", "..", "spec",
                                       "amazon_currency.json")
        with open(currency_file, "r") as fp:
            return json.load(fp)
  
    def availability_countries(self):
        return self._availability_countries("amazon_countries.json")

    def include_content(self):
        content_inc = self.obj.application["content-description"]["included-activities"]
        return [
            "false" if content_inc["account-creation"] == "no" else "true", 
            "false" if content_inc["advertising"] == "no" else "true", 
            "false" if content_inc["gambling"] == "no" else "true", 
            "false" if content_inc["personal-information-collection"] == "no" else "true", 
            "false" if content_inc["user-to-user-communications"] == "no" 
                and content_inc["user-generated-content"] == "no" else "true"
        ]
    
    def free_app_of_day(self):
        if hasattr(self.obj.application, "store-specific") and hasattr(self.obj.application["store-specific"], "amazon"):
                if hasattr(self.obj.application["store-specific"]["amazon"], "free-app-of-the-day-eligibility"):
                    return self.obj.application["store-specific"]["amazon"]["free-app-of-the-day-eligibility"] == "yes"
        return False
        
    def content_desc(self):
        content = self.obj.application["content-description"]["content-descriptors"]
        alchohol = [
            self.exchange(content["drugs"]),
            self.exchange(content["alcohol"]),
            self.exchange(content["smoking"])
        ]
        cartoon_violance = self.exchange(content["cartoon-violence"])
        intolerance = self.exchange(content["discrimination"])
        real_violance = self.exchange(content["realistic-violence"])
        sexual_content = self.exchange(content["sexual-content"])
        nudity = sexual_content
        #TODO
        #bad-language
        #fear
        #gambling-reference
        
        return [
            str(max(alchohol)),
            str(cartoon_violance),
            str(intolerance),
            str(nudity),
            "0", #Profanity or crude humor
            str(real_violance),
            str(sexual_content),
        ]

    def exchange(self, data):
        return 0 if data == "no" else 1 if data == "light" else 2
    
    def rating(self):
        rating = super(Amazon, self).rating()

        return {
            "3": "SUITABLE_FOR_ALL",
            "6": "PRE_TEEN",
            "10": "TEEN",
            "13": "TEEN",
            "17": "MATURE",
            "18": "MATURE"
        }[rating]

    def small_app_icon_path(self):
        app_icon_path = self.app_icon_path()
        small_icon_path = os.path.join(os.path.dirname(app_icon_path), "small_icon.png")
        image_resizer.resize(app_icon_path, small_icon_path, 114, 114)
        return small_icon_path

    def binary_alias(self):
        if hasattr(self.obj.application, "store-specific") and hasattr(self.obj.application["store-specific"], "amazon"):
            return self.obj.application["store-specific"]["amazon"]["binary-alias"]
        return "binary"

    def apply_amazon_drm(self):
        if hasattr(self.obj.application, "store-specific") and hasattr(self.obj.application["store-specific"], "amazon"):
            return self.obj.application["store-specific"]["amazon"]["apply-amazon-drm"] == "yes"
        return False
    
    def kindle_fire_first_generation(self):
        if hasattr(self.obj.application, "store-specific") and hasattr(self.obj.application["store-specific"], "amazon"):
            return self.obj.application["store-specific"]["amazon"]["kindle-support"]["kindle-fire-first-generation"] == "yes"
        return False

    def kindle_fire(self):
        if hasattr(self.obj.application, "store-specific") and hasattr(self.obj.application["store-specific"], "amazon"):
            return self.obj.application["store-specific"]["amazon"]["kindle-support"]["kindle-fire"] == "yes"
        return False

    def kindle_fire_hd(self):
        if hasattr(self.obj.application, "store-specific") and hasattr(self.obj.application["store-specific"], "amazon"):
            return self.obj.application["store-specific"]["amazon"]["kindle-support"]["kindle-fire-hd"] == "yes"
        return False

    def kindle_fire_hd_89(self):
        if hasattr(self.obj.application, "store-specific") and hasattr(self.obj.application["store-specific"], "amazon"):
            return self.obj.application["store-specific"]["amazon"]["kindle-support"]["kindle-fire-hd-8-9"] == "yes"
        return False
        
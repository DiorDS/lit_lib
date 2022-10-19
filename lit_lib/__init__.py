import json
from ast import List
from enum import Enum
from pathlib import Path
from sys import stderr
from typing import Dict, Optional, Union

from deep_translator import GoogleTranslator


class NotFoundInstruction(Enum):
    TRANSLATE = 1
    TRANSLITERATE = 2
    NONE = 3


class LitLanguage:
    def __init__(self, name: str, phrases: dict, not_found_instructions: NotFoundInstruction=NotFoundInstruction.TRANSLATE):
        """
        Initialize the class

        :param name: The name of the language
        :param phrases: The phrases of the language
        :param not_found_instructions: The instructions to be executed when a phrase is not found
        """
        self.name = name
        self.phrases = phrases
        self.not_found_instructions = not_found_instructions


    def __getitem__(self, key: str) -> Optional[str]:
        """
        Get the translation of the given key.

        Args:
            key: The key to translate.

        Returns:
            The translation of the given key.
        """
        if key not in self.phrases.keys() and self.not_found_instructions == NotFoundInstruction.NONE:
            raise KeyError(f"Phrase {key} not found in language {self.name}")

        result = self.phrases.get(key)

        if self.not_found_instructions == NotFoundInstruction.TRANSLITERATE and result is None:
            result = self._translit(key)
        
        if self.not_found_instructions == NotFoundInstruction.TRANSLATE and result is None:
            result = Lit._translate(self.name, key)
            self.phrases[key] = result
        
        return result
    
    def _translit(self, key: str) -> str:  # type: ignore
        """
        Transliterate the given key.

        Args:
            key: The key to transliterate.

        Returns:
            The transliterated key.
        """
        return key

    def __contains__(self, key: str) -> bool:
        """
        Check if the key is in the phrases or if auto transliteration is enabled.

        :param key: The key to check.
        :return: True if the key is in the phrases or if auto transliteration is enabled.
        """
        return key in self.phrases.keys() or self.auto_translit
    
    def __repr__(self) -> str:
        return f"<LitLanguage name={self.name}>"
    
    def compile(self) -> str:
        """
        Compile the current object into a JSON string.

        :return: The JSON string.
        """
        result = {
            "name": self.name,
            "phrases": self.phrases
        }
        return result


class Lit:
    def __init__(self, config_path: Union[str, Path], not_found_instructions: NotFoundInstruction = NotFoundInstruction.TRANSLATE, json_as_str: str = None, diasble_warnings: bool = False) -> None:
        """
        Initialize the Config class

        :param config_path: Path to the config file
        :param not_found_instructions: What to do if a key is not found in the config file
        :param json_as_str: JSON string to use as config
        :param diasble_warnings: Disable warnings
        """
        self.warnings = diasble_warnings
        
        if json_as_str is not None:
            self.config = json.loads(json_as_str)
            self.config_path = "JSON_STRING"
            
        elif config_path is Path:
            if self.warnings:
                print("WRNING: Dont use file config for production applications (use json_as_str)!",file=stderr)
            self.config_path = config_path
            
        else:
            if self.warnings:
                print("WRNING: Dont use file config for production applications (use json_as_str)!",file=stderr)
            self.config_path = Path(config_path)
        
        if self.config_path != "JSON_STRING":
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file {self.config_path} not found")

            self.not_found_instructions = not_found_instructions
            self.config = self._load_config()
            self.langs = []

    def _load_config(self) -> dict:
        with self.config_path.open(encoding="utf-8") as f:
            try:
                return json.load(f)

            except json.decoder.JSONDecodeError:
                raise ValueError(f"Config file {self.config_path} is not" 
                                 f" a valid JSON file")
            
    
    def __repr__(self) -> str:
        return f"<Lit config_path={self.config_path}>"
    
    def get(self, key: str, language: str) -> str:  # type: ignore
        """
        Get the value of the key in the language.

        Args:
            key: The key to get the value of.
            language: The language to get the value in.

        Returns:
            The value of the key in the language.
        """
        return self[language][key]

    def __getitem__(self, key: str) -> LitLanguage:  # type: ignore
        """
        Get a language from the config file.

        Args:
            key: The name of the language to get.

        Returns:
            The language object.

        Raises:
            KeyError: If the language is not found in the config file.
        """
        if key not in self.config and self.not_found_instructions == NotFoundInstruction.NONE:
            raise KeyError(f"Language {key} not found in config file")
        

        res = LitLanguage(key, self.config.get(key, {}), not_found_instructions= self.not_found_instructions)
        self.langs.append(res)
        return res

    def __setitem__(self, key: str, phrases: list[tuple[str, str]]) -> None:
        """
        Add a new key to the config dictionary.

        Args:
            key: The key to add to the config dictionary.
            phrases: A list of tuples containing the phrase to translate and the alias to use.
        """
        res_dict = {}
        for k, alias in phrases:
            res_dict[alias] = self._translate(key, k)

        if key in self.config.keys():
            self.config[key].update(res_dict)
        else:
            self.config[key] = res_dict

    @staticmethod
    def _translate(lang: str, phrase: str) -> str:
        translator = GoogleTranslator(source='auto', target=lang.lower())
        result = translator.translate(phrase)

        return result
    
    def compile_all(self) -> List[Dict]:
        """
        Compile all languages.

        Returns:
            List[Dict]: A list of dictionaries containing the compiled languages.
        """
        result = []

        for i in self.langs:
            result.append(i.compile())
    
        return result

def lang_from_compiled_dict(settings: dict) -> LitLanguage:
    return LitLanguage(settings["name"], settings["phrases"])
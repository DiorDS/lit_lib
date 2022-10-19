import json
from enum import Enum
from pathlib import Path
from sys import stderr
from typing import Union

from deep_translator import GoogleTranslator

TRANSLIT = "TRANSLIT"

ru_to_en = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "j",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "x",
    "ц": "c",
    "ч": "ch",
    "ш": "sh",
    "щ": "ssh",                        
    "ъ": "",                        
    "ы": "y`",                        
    "ь": "",                        
    "э": "e`",
    "ю": "yy",
    "я": "ya"
}

class NotFoundInstruction(Enum):
    TRANSLATE = 1
    TRANSLITERATE = 2
    NONE = 3


class LitLanguage:
    def __init__(self, name: str, phrases: dict, not_found_instructions: NotFoundInstruction= NotFoundInstruction.TRANSLATE):
        """
        Initialize the class.

        Args:
            name: The name of the language.
            phrases: The phrases of the language.
            auto_translit: Whether to automatically transliterate the language.
        """
        self.name = name
        self.phrases = phrases
        self.not_found_instructions = not_found_instructions

    def __getitem__(self, key: str) -> str:
        """Get a phrase from the language.

        Args:
            key (str): The phrase key.

        Returns:
            str: The phrase.

        Raises:
            KeyError: If the phrase key is not found and auto_translit is disabled.
        """

        print(self.not_found_instructions)
        if key not in self.phrases and self.not_found_instructions == NotFoundInstruction.NONE:
            raise KeyError(f"Phrase {key} not found in language {self.name}")

        result = self.phrases.get(key)

        if self.not_found_instructions == NotFoundInstruction.TRANSLITERATE and result is None:
            result = self._translit(key)
        
        if self.not_found_instructions == NotFoundInstruction.TRANSLATE and result is None:
            result = Lit._translate(self.name, key)
            self.phrases[key] = result
        
        return result
    
    def _translit(self, key: str) -> str:
        """
        Transliterate the given key to the corresponding value.

        Args:
            key: The key to transliterate.

        Returns:
            The transliterated value.
        """
        return key

    def __contains__(self, key: str) -> bool:
        """Check if a phrase is in the language.

        Args:
            key (str): The phrase key.

        Returns:
            bool: True if the phrase is in the language, False otherwise.
        """

        return key in self.phrases or self.auto_translit
    
    def __repr__(self) -> str:
        return f"<LitLanguage name={self.name}>"

class Lit:
    def __init__(self, config_path: Union[str, Path], not_found_instructions: NotFoundInstruction = NotFoundInstruction.TRANSLATE, json_as_str: str = None, diasble_warnings: bool = False):
        """
        Initialize the class

        Args:
            config_path (str or Path): Path to the config file
            auto_translit (bool): Enable auto transliteration
            json_as_str (str or None): JSON string
            diasble_warnings (bool): Disable warnings
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

    def _load_config(self) -> dict:
        """Load the configuration file.

        Returns:
            dict: The configuration file as a dictionary.

        Raises:
            ValueError: If the configuration file is not a valid JSON file.
        """

        with self.config_path.open(encoding="utf-8") as f:
            try:
                return json.load(f)

            except json.decoder.JSONDecodeError:
                raise ValueError(f"Config file {self.config_path} is not" 
                                 f" a valid JSON file")
            
    
    def __repr__(self) -> str:
        return f"<Lit config_path={self.config_path}>"
    
    def get(self, key: str, language: str) -> str:
        """
        Get the value of the key in the language.

        Args:
            key: The key to get the value of.
            language: The language to get the value in.

        Returns:
            The value of the key in the language.
        """
        return self[language][key]

    def __getitem__(self, key: str) -> LitLanguage:
        """Get a language from the configuration file.

        Args:
            key (str): The language key.

        Returns:
            LitLanguage: The language.

        Raises:
            KeyError: If the language key is not found and auto_translit is disabled"""
        
        if key not in self.config and self.not_found_instructions == NotFoundInstruction.NONE:
            raise KeyError(f"Language {key} not found in config file")
            
        return LitLanguage(key, self.config.get(key, []), not_found_instructions= self.not_found_instructions)

    def __setitem__(self, key: str, phrases: list[tuple]) -> None:
        """
        Add a new key to the config dictionary.

        Args:
            key: The key to add to the config dictionary.
            phrases: A list of tuples containing the phrase to translate and
                the alias to use for the translated phrase.

        Returns:
            None
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
        """Translate a word to the given language.

        Args:
            lang (LitLanguage): The language to translate to.
            phrase (str): The phrase to translate.

        Returns:
            str: The translated phrase.
        """

        translator = GoogleTranslator(source='auto', target=lang.lower())
        result = translator.translate(phrase)

        return result
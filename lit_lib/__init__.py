import json
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Union

from deep_translator import GoogleTranslator


class NotFoundInstruction(Enum):
    TRANSLATE = 1
    TRANSLITERATE = 2
    NONE = 3


class LitLanguage:
    def __init__(self,
        name: str,
        phrases: Dict[str, str], 
        not_found_instructions: NotFoundInstruction= NotFoundInstruction.TRANSLATE
    ):
        """
        Represents a phrase in a language.

        Attributes:
            name: The name of the phrase.
            phrases: The phrases in the language.
            not_found_instructions: The instructions to follow when a phrase is not found.
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

        nfi = self.not_found_instructions == NotFoundInstruction.NONE
        if key not in self.phrases.keys() and nfi:
            raise KeyError(f"Phrase {key} not found in language {self.name}")

        result = self.phrases.get(key)
        nfi = self.not_found_instructions == NotFoundInstruction.TRANSLITERATE
        if nfi and result is None:
            result = self._translit(key)

        nfi = self.not_found_instructions == NotFoundInstruction.TRANSLATE
        if nfi and result is None:
            result = Lit._translate(self.name, key)
            self.phrases[key] = result
        
        return result
    
    def _translit(self, key: str) -> str:
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
        Check if the key is in the dictionary.

        Args:
            key: The key to check.

        Returns:
            True if the key is in the dictionary, False otherwise.
        """
        
        return key in self.phrases.keys() or not self.not_found_instructions == NotFoundInstruction.NONE
    
    def __repr__(self) -> str:
        return f"<LitLanguage name={self.name}>"
    
    def compile(self) -> Dict:
        result = {
            "name": self.name,
            "phrases": self.phrases
        }
        return result


class Lit:
    def __init__(
            self, 
            config_path: Union[str, Path], 
            not_found_instructions: NotFoundInstruction = NotFoundInstruction.TRANSLATE, 
            json_as_str: str = None, 
            diasble_warnings: bool = False
        ) -> None:
        """
        Initialize the class.

        Args:
            config_path: Path to the config file.
            not_found_instructions: Instructions for the not found keys.
            json_as_str: JSON string.
            diasble_warnings: Disable warnings.
        """
        self.warnings = diasble_warnings
        
        if json_as_str is not None:
            self.config = json.loads(json_as_str)
            self.config_path = "JSON_STRING"
            
        elif config_path is Path:
            if self.warnings:
                print("WARNING: Dont use file config for production applications (use json_as_str)!")
            self.config_path = config_path
            
        else:
            if self.warnings:
                print("WARNING: Dont use file config for production applications (use json_as_str)!")
            self.config_path = Path(config_path)
        
        if self.config_path != "JSON_STRING":
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file {self.config_path} not found")

            self.not_found_instructions = not_found_instructions
            self.config = self._load_config()
            self.langs = {}

    def _load_config(self) -> dict:
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
        
        if key not in self.langs.values():
            res = LitLanguage(key, self.config.get(key, {}), not_found_instructions= self.not_found_instructions)
            self.langs[key] = res


        return self.langs[key]

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
    
    def compile_all(self) -> list[Dict]:
        """
        Compile all languages.

        Returns:
            list[Dict]: A list of dictionaries containing the compiled languages.
        """
        result = []

        for i in self.langs.values():
            result.append(i.compile())
    
        return result

def lang_from_compiled_dict(settings: dict) -> LitLanguage:
    return LitLanguage(settings["name"], settings["phrases"])

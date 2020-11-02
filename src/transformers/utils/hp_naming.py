import copy
import re


class TrialShortNamer:
    PREFIX = "hp"
    DEFAULTS = dict()
    NAMING_INFO = None

    @classmethod
    def set_defaults(cls, prefix, defaults):
        cls.PREFIX = prefix
        cls.DEFAULTS = defaults
        cls.build_naming_info()

    @staticmethod
    def shortname_for_word(info, word):
        if len(word) == 0:
            return ""
        short_word = None

        if word in info["short_word"]:
            return info["short_word"][word]
        for prefix_len in range(1, len(word) + 1):
            prefix = word[:prefix_len]
            if prefix in info["reverse_short_word"]:
                continue
            else:
                short_word = prefix
                break

        if short_word is None:
            # Paranoid fallback
            def int_to_alphabetic(integer):
                s = ""
                while integer != 0:
                    s = chr(ord("A") + integer % 10) + s
                    integer //= 10
                return s

            i = 0
            while True:
                sword = word + "#" + int_to_alphabetic(i)
                if sword in info["reverse_short_word"]:
                    continue
                else:
                    short_word = sword
                    break

        info["short_word"][word] = short_word
        info["reverse_short_word"][short_word] = word

        return short_word

    @staticmethod
    def shortname_for_key(info, param_name):
        words = param_name.split("_")

        shortname_parts = [TrialShortNamer.shortname_for_word(info, word) for word in words]

        # We try to create a separatorless short name, but if there is a collision we have to fallback
        # to a separated short name

        separators = ("", "_")

        for separator in separators:
            shortname = separator.join(shortname_parts)
            if shortname not in info["reverse_short_param"]:
                info["short_param"][param_name] = shortname
                info["reverse_short_param"][shortname] = param_name
                return shortname

        return param_name

    @staticmethod
    def add_new_param_name(info, param_name):
        short_name = TrialShortNamer.shortname_for_key(info, param_name)
        info["short_param"][param_name] = short_name
        info["reverse_short_param"][short_name] = param_name

    @classmethod
    def build_naming_info(cls):
        if cls.NAMING_INFO is not None:
            return

        info = dict(
            short_word={},
            reverse_short_word={},
            short_param={},
            reverse_short_param={},
        )

        field_keys = list(cls.DEFAULTS.keys())

        for k in field_keys:
            cls.add_new_param_name(info, k)

        cls.NAMING_INFO = info

    @classmethod
    def shortname(cls, params):
        cls.build_naming_info()
        assert cls.PREFIX is not None
        name = [copy.copy(cls.PREFIX)]

        missing_defaults = dict()
        for k, v in params.items():
            if k not in cls.DEFAULTS:
                missing_defaults[k] = v

        if len(missing_defaults) != 0:
            keys = list(missing_defaults.keys())
            keys.sort()
            missing_defaults = {k: missing_defaults[k] for k in keys}
            message = "dict(" + "".join(f"{k}={repr(v)},\n" for k, v in missing_defaults.items()) + ")"
            raise Exception(
                f"You should provide a additional default values in your TrialShortNamer subclass.\n Suggested default dictionary:\n{message}\n"
            )

        for k, v in params.items():
            if v == cls.DEFAULTS[k]:
                # The default value is not added to the name
                continue

            key = cls.NAMING_INFO["short_param"][k]

            if isinstance(v, bool):
                v = 1 if v else 0

            if any(char.isdigit() for char in k):
                sep = "-"
            else:
                sep = "" if isinstance(v, (int, float)) else "-"
            e = f"{key}{sep}{v}"
            name.append(e)

        return "_".join(name)

    @classmethod
    def parse_repr(cls, repr):
        # This code should have some tests before usage
        assert False
        repr = repr[len(cls.PREFIX) + 1 :]
        if repr == "":
            values = []
        else:
            values = repr.split("_")

        parameters = {}

        for value in values:
            if "-" in value:
                parts = value.split("-")
                last_part = parts[-1]
                try:
                    p_v = -float(last_part)
                except ValueError:
                    p_v = last_part

                p_k = "-".join(parts[:-1])
            else:
                p_k = re.sub("[0-9.]", "", value)
                p_v = float(re.sub("[^0-9.]", "", value))

            key = cls.NAMING_INFO["reverse_short_param"][p_k]

            parameters[key] = p_v

        for k in cls.DEFAULTS:
            if k not in parameters:
                parameters[k] = cls.DEFAULTS[k]

        return parameters

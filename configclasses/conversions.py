from decimal import Decimal


def to_bool(value):
    """
    Convert a bool, string type or numeric type to a bool.

    raises: ValueError on invalid values
            TypeError on invalid `value` types.
    """
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        upper = value.upper()
        if upper in ["TRUE", "1"]:
            return True
        elif upper in ["FALSE", "0"]:
            return False
        else:
            # TODO tell the user what field this is
            raise ValueError(f"{value} is not a valid boolean value")
    elif isinstance(value, (bytes, bytearray)):
        upper = value.upper()
        if upper in [b"TRUE", b"1"]:
            return True
        elif upper in [b"FALSE", b"0"]:
            return False
        else:
            # TODO tell the user what field this is
            raise ValueError(f"{value} is not a valid boolean value")
    elif isinstance(value, (int, float, Decimal)):
        if value == 0:
            return False
        elif value == 1:
            return True
        else:
            raise ValueError(f"{value} is not a valid boolean value")
    raise TypeError(f"{type(value)} cannot be converted to a bool")


class EnumConversionRegistry():
    def __init__(self):
        self.name_mappings = {}
        self.value_mappings = {}

    def add_enum(self, enum):
        self.value_mappings[enum] = {variant.value: variant.value for variant in enum}
        
        variants_by_name = {}
        for variant in enum:
            variants_by_name[variant.name.upper()] = variant.name
            value = str(variant.value).upper()
            self.value_mappings[enum][value] = variant.value
        self.name_mappings[enum] = variants_by_name

    def to_enum(self, enum, raw_value):
        if not (enum in self.name_mappings and enum in self.value_mappings):
            raise ValueError(f"Enum type {enum} not registered")
        # Uppercase string type raw values
        if isinstance(raw_value, (str, bytes, bytearray)):
            canonical = raw_value.upper()
        else:
            canonical = raw_value

        if canonical in self.name_mappings[enum]:
            name = self.name_mappings[enum][canonical]
            return enum[name]
        elif canonical in self.value_mappings[enum]:
            value = self.value_mappings[enum][canonical]
            return enum(value)
        else:
            raise ValueError(f"Invalid value {raw_value} for Enum {enum}")


def quote_stripped(value):
    """
    Strip out a single level of single (') or double (") quotes.
    """
    single, double = "'", '"'
    if (value.startswith(single) and value.endswith(single)) or\
       (value.startswith(double) and value.endswith(double)):
        return value[1:-1]
    return value


def kv_list(str_value):
    """
    Kv lists are comma seperated pairs of values where a pair is defined as
    `key=value`. For example: "a=1,b=2" -> {"a": 1, "b": 2}.

    Whitespace around a key or value is stripped unless text is quoted.

    Skips empty pairs and raises an exception on any other malformed pair
    """
    kv = {}
    for pair in str_value.split(","):
        if not pair.strip():
            continue  # Skip empty pairs
        # TODO: Raise more helpful exception on bad split
        key, value = pair.split("=", 1)
        key, value = key.strip(), value.strip()
        key, value = quote_stripped(key), quote_stripped(value)
        kv[key] = value

    return kv

    # return {item.split("=")[0]: item.split("=")[1] for item in str_value.split()}

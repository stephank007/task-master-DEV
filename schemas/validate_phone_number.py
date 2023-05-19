import phonenumbers
from pydantic.validators import strict_str_validator

class PhoneNumber(str):
    """Phone Number Pydantic type, using google's phonenumbers"""

    @classmethod
    def __get_validators__(cls):
        yield strict_str_validator
        yield cls.validate

    @classmethod
    def validate(cls, v: str):
        # Remove spaces
        v = v.strip().replace(' ', '')
        try:
            pn = phonenumbers.parse(v)
            x = len(str(pn.national_number))
        except phonenumbers.phonenumberutil.NumberParseException:
            raise ValueError('invalid phone number format')
        if not 9 <= x <= 10:
            raise ValueError('please check your phone number')

        return cls(phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.NATIONAL))

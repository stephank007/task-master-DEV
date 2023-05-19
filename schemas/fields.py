import re
from enum import Enum
from pydantic import BaseModel, EmailStr, validator, constr, Field, ValidationError
from schemas.validate_phone_number import PhoneNumber
from typing import Optional
from datetime import datetime
import pandas as pd
from devtools import debug

# password_regex = "((?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[\W]).{8,64})"
password_regex = "((?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{6,64})"
username_regex = '[a-z]{5,8}'
class ExtendedEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

class Role(str, ExtendedEnum):
    R_01 = 'normal'
    R_02 = 'status_updater'
    R_03 = 'admin'

class Source(str, ExtendedEnum):
    logmar           = 'רע"ן לוגמ"ר'
    maam             = 'רע"ן מע"מ'
    cdr_round_tables = 'שולחנות עגולים CDR'
    logmar_issues    = 'נושאים פתוחים לוגמ"ר'
    pdr_round_tables = 'PDR RoundTable'

class Department(str, ExtendedEnum):
    D_01 = 'אמל״ח'
    D_02 = 'לוגמ״ר'
    D_03 = 'מפקדה'
    D_04 = 'רוזנשטוק'
    D_05 = 'מנהלת'
    D_06 = 'M4N'
    D_07 = 'חטלו״ג'

class WMSDomain(str, ExtendedEnum):
    so = 'אספקה יוצאת'
    si = 'אספקה נכנסת'
    sm = 'ניהול המלאי'
    dm = 'ניהול הפצה'
    ym = 'ניהול החצר'
    ct = 'תשתיות'

class Status(str, ExtendedEnum):
    P_01 = 'פתוח'
    P_02 = 'בוצע'
    P_03 = 'מבוטל'
    P_04 = 'עתידי'
    #
    P_10 = 'טרם החל'
    P_11 = 'בבדיקה'
    P_12 = 'בוצע בהצלחה'
    #
    P_15 = 'אין הערות'
    P_16 = 'פתור'  # documentation notes are resolved

class Priority(str, ExtendedEnum):
    S_01 = 'נמוך'
    S_02 = 'בינוני'
    S_03 = 'גבוה'
    S_04 = 'קריטי'

class SAPDomainEnum(str, ExtendedEnum):
    D_01  = '01: מלאי ואחסנה'
    D_02  = '02: שרשרת אספקה'
    D_03  = '03: אחזקה'
    D_04  = '04: תקציב ורכש'
    D_06  = '06: קטלוג'
    D_07  = '07: הובלה'
    D_10  = '10: רחבי'

class SAPProcessEnum(str, ExtendedEnum):
    P_01_01  = '01.01: קבלה מרכש'
    P_01_02  = '01.02: ערכות'
    P_01_03  = '01.03: חיובים וזיכויים'
    P_01_04  = '01.04: השקעות ופירוקים'
    P_01_05  = '01.05: ויסותים פנימיים'
    P_01_06  = '01.06: אחסנה'
    P_01_07  = '01.07: חוקת המלאי'
    P_01_11  = '01.11: ספירות'
    P_01_12  = '01.12: גריטות והשמדות'
    P_01_14  = '01.14: מבנה ארגוני'
    P_01_15  = '01.15: כושרים'
    P_01_16  = '01.16: המרות טכניות'
    P_01_17  = '01.17: סדרות'
    P_01_18  = '01.18: בימ"לים'
    P_02_01  = '02.01: מבנה ארגוני -  שרשרת'
    P_02_02  = '02.02: אספקה ליחידות'
    P_02_04  = '02.04: ויסות פנים ובין מרחבים'
    P_02_06  = '02.06: החזרות מיחידות'
    P_02_08  = '02.08: מכירות'
    P_02_11  = '02.11: החלפות'
    P_02_12  = '02.12: תיקונים'
    P_02_13  = '02.13: השאלות'
    P_02_18  = '02.18: טיפול בהפרשים'
    P_02_21  = '02.21: רענון ערכות של יחידות'
    P_02_23  = '02.23: MRP'
    P_02_24  = '02.24: אספקה ללא סימוכין'
    P_03_01  = '03.01: שכר עידוד'
    P_03_02  = '03.02: בחינה קבלה מרכש'
    P_03_03  = '03.03: אחזקה MasterData'
    P_04_01  = '04.01: מבנה ארגוני - תקציב ורכש'
    P_04_02  = '04.02: סבב אישורים'
    P_04_03  = '04.03: הזמנה פנימית'
    P_04_04  = '04.04: רכש חו"ל'
    P_06_01  = '06.01: מבנה ארגוני - קטלוג'
    P_06_02  = '06.02: ממשק נתוני קטלוג לזכיין'
    P_06_03  = '06.03: שינויים במערכות הקטלוג'
    P_07_01  = '07.01: הפצה'

class SAPDomainModel(BaseModel):
    full_name: SAPDomainEnum
    id       : str
    name     : str

    def get_full_name(self):
        return self.full_name

class SAPProcessModel(BaseModel):
    full_name: SAPProcessEnum
    id       : str
    name     : str
    parent   : SAPDomainEnum

class OwnerNote(BaseModel):
    note_id    : Optional[str]
    note_date  : Optional[str]
    note       : Optional[str]

class NoteModel(BaseModel):
    main_note      : str
    secondary_note : Optional[str]

class ReferenceModel(BaseModel):
    source     : Source
    sheet      : Optional[str]
    old_user   : Optional[str]
    record_type: str

class UserModel(BaseModel):
    full_name   : str
    email       : EmailStr
    tn          : PhoneNumber
    department  : Department
    role        : Optional[Role]

    # @validator('user_name')
    @validator('full_name')
    def name_must_contain_space(cls, v):
        if ' ' not in v:
            raise ValueError('full name must contain a space')
        else:
            return v

    @validator('department')
    def department_printable(cls, v: str):
        assert v.isprintable(), 'must be printable'
        return v

class LoginModel(UserModel, BaseModel):
    # username  : constr(min_length=5, max_length=10, to_lower=True)
    # username  : str = Field(..., regex=username_regex)
    # password  : str = Field(..., regex=password_regex)
    username  : str
    password  : str
    v_password: str
    signup_ts : datetime = None

    @validator('username')
    def username_check(cls, v):
        pattern = re.compile(username_regex)
        if not pattern.match(v):
            raise ValueError('must be between 5-8 chars long all in lowercase')
        else:
            return v

    @validator('password')
    def password_check(cls, v):
        pattern = re.compile(password_regex)
        if not pattern.match(v):
            raise ValueError('must have at least: 6 chars long, 1 uppercase and 1 number ')
        else:
            return v

    @validator('v_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('passwords do not match')
        return v
    
    @validator('username')
    def must_not_contain_space(cls, v):
        if ' ' in v:
            raise ValueError('username cannot have space')
        else:
            return v

class ResetLoginModel(BaseModel):
    password  : str = Field(..., regex=password_regex)
    v_password: str

    @validator('v_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('passwords do not match')
        return v

class TaskUpdateModel(BaseModel):
    owner_note: str
    user_name : str
    role      : str
    owner_name: str
    status    : Optional[Status]
    priority  : Optional[Priority]
    due_date  : Optional[str]
    sheet     : Optional[str]
    row_id    : str

    @validator('due_date')
    def validate_due_date(cls, v):
        try:
            if v:
                dt = pd.to_datetime(v, format='%d/%m/%Y').strftime('%Y-%m-%d'),
                return dt
        except Exception as ex:
            raise ValueError('correct format: dd/mm/yyyy')

    @validator('status')
    def validate_update_privilege(cls, v, values):
        if v is None or values['role'] in [Role.R_02, Role.R_03]:
            return
        else:
            raise ValueError('<- only admin users can change status')

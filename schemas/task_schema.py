from pydantic import BaseModel, validator
from typing import List, Optional
from schemas.fields import SAPDomainModel, SAPProcessModel, WMSDomain, UserModel, NoteModel, Status,\
    Priority, ReferenceModel, OwnerNote
from schemas.mongo_schema import MongoManager


class TaskModel(BaseModel):
    row_number  : int
    reference   : ReferenceModel
    sap_domain  : Optional[SAPDomainModel]
    sap_process : Optional[SAPProcessModel]
    wms_domain  : WMSDomain
    subject     : str
    status      : Status
    user_name   : UserModel
    priority    : Optional[Priority]
    note        : NoteModel
    owner_notes : Optional[List[OwnerNote]]
    start       : Optional[str]
    finish      : Optional[str]
    due_date    : Optional[str]

    @validator('sap_domain', pre=True, each_item=True)
    def parse_each_domain(cls, d):
        domain_elements = d.split(': ')
        domain = SAPDomainModel(full_name=d, id=domain_elements[0], name=domain_elements[1])
        return domain

    @validator('sap_process', pre=True, each_item=True)
    def parse_each_process(cls, d, values, **kwargs):
        process_elements = d.split(': ')
        process = SAPProcessModel(
            full_name=d,
            id=process_elements[0],
            name=process_elements[1],
            parent=values['sap_domain'].full_name
        )
        return process

    @validator('priority')
    def source_printable(cls, v: str):
        assert v.isprintable(), 'must be printable'
        return v

    class Config:
        title = 'Task Schema'
        # The ObjectIdField creates an bson ObjectId value, so its necessary to setup the json encoding
        # json_encoders = {ObjectId: str}

class TaskSchema(MongoManager):
    def get_db_name(self):
        print(3*'\n', self._db)

# print(TaskModel.schema_json(indent=4, ensure_ascii=False).encode('utf-8').decode())

from enum import Enum


# Kept as (str, Enum) rather than StrEnum: StrEnum changes f-string/str() output from
# "ProtectedCharacteristic.AGE" to "Age", which would alter generated file names and log output.
class ProtectedCharacteristic(str, Enum):  # noqa: UP042
    AGE = "Age"
    DISABILITY = "Disability"
    GENDER_REASSIGNMENT = "Gender Reassignment"
    MARRIAGE_CIVIL_PARTNERSHIP = "Marriage and Civil Partnership"
    PREGNANCY_MATERNITY = "Pregnancy and Maternity"
    RACE = "Race"
    RELIGION_BELIEF = "Religion or Belief"
    SEX = "Sex"
    SEXUAL_ORIENTATION = "Sexual Orientation"

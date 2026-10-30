from enum import Enum


class ProtectedCharacteristic(str, Enum):
    AGE = "Age"
    DISABILITY = "Disability"
    GENDER_REASSIGNMENT = "Gender Reassignment"
    MARRIAGE_CIVIL_PARTNERSHIP = "Marriage and Civil Partnership"
    PREGNANCY_MATERNITY = "Pregnancy and Maternity"
    RACE = "Race"
    RELIGION_BELIEF = "Religion or Belief"
    SEX = "Sex"
    SEXUAL_ORIENTATION = "Sexual Orientation"

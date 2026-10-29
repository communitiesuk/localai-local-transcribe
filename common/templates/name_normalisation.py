# Python and Postgres normalisation must use the same rules
TEMPLATE_NAME_TRIM_CHARS = " \t\n\r"
TEMPLATE_NAME_TRIM_CHARS_SQL = r"E' \t\n\r'"
USER_TEMPLATE_NORMALISED_NAME_UNIQUE_INDEX = "uq_user_template_user_id_normalised_name"


def normalise_template_name(name: str) -> str:
    return name.strip(TEMPLATE_NAME_TRIM_CHARS).lower()

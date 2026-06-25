type OrganisationOptionProps = {
    id: string
    name: string
}

export default function OrganisationOption({
    id,
    name,
}: OrganisationOptionProps) {
    return <option value={id}>{name}</option>
}
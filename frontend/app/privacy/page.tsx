import { GovukHeading, GovukList, GovukListItem } from '@/components/govuk'

export const metadata = {
  title: 'Privacy notice for Local Transcribe',
}

export default function PrivacyPage() {
  return (
    <div className="govuk-grid-row">
      <div className="govuk-grid-column-two-thirds">
        <GovukHeading as="h1" size="l">
          Privacy notice for Local Transcribe
        </GovukHeading>

        <p className="govuk-body">This privacy notice:</p>
        <GovukList type="bullet">
          <GovukListItem>explains your rights</GovukListItem>
          <GovukListItem>
            provides the information you’re entitled to under UK data protection
            legislation
          </GovukListItem>
        </GovukList>

        <GovukHeading as="h2" size="m">
          What Local Transcribe is
        </GovukHeading>
        <p className="govuk-body">
          Local Transcribe is an AI transcription and summarisation tool. It
          uses audio recordings of conversations to generate transcripts and
          summaries. A transcript is a word for word text version of your
          conversation.
        </p>
        <p className="govuk-body">
          Local Transcribe is being adopted by frontline workers in some local
          government departments.
        </p>

        <GovukHeading as="h2" size="m">
          Who we are
        </GovukHeading>
        <p className="govuk-body">
          Local Transcribe is owned and operated by the Local AI programme in
          the Ministry for Housing, Communities and Local Government (MHCLG).
        </p>
        <p className="govuk-body">
          Your council has signed a data sharing agreement with MHCLG so that
          you can use Local Transcribe. MHCLG and your council are joint data
          controllers.
        </p>
        <p className="govuk-body">You can contact the:</p>
        <GovukList type="bullet">
          <GovukListItem>
            Local Transcribe team:{' '}
            <a className="govuk-link" href="mailto:localai@communities.gov.uk">
              localai@communities.gov.uk
            </a>
          </GovukListItem>
          <GovukListItem>
            MHCLG data protection officer:{' '}
            <a
              className="govuk-link"
              href="mailto:dataprotection@communities.gov.uk"
            >
              dataprotection@communities.gov.uk
            </a>
          </GovukListItem>
        </GovukList>

        <GovukHeading as="h2" size="m">
          Why we collect your personal information
        </GovukHeading>
        <p className="govuk-body">
          We process your personal data while you’re using the Local Transcribe
          product, and during activities that support the product.
        </p>
        <p className="govuk-body">This includes, but is not limited to:</p>
        <GovukList type="bullet">
          <GovukListItem>testing and collecting user feedback</GovukListItem>
          <GovukListItem>user research and design</GovukListItem>
          <GovukListItem>
            engaging with your council’s employees, personnel, team managers and
            frontline workers
          </GovukListItem>
          <GovukListItem>onboarding users</GovukListItem>
          <GovukListItem>
            sharing audio data, survey data or data from council case management
            systems between your council and MHCLG – for example, to support
            operational testing or evaluate the accuracy of Local Transcribe’s
            AI outputs
          </GovukListItem>
          <GovukListItem>
            service improvement metrics, value benefit metrics and analytics
          </GovukListItem>
          <GovukListItem>
            Local Transcribe team members accessing data within the tool to help
            them support users
          </GovukListItem>
        </GovukList>

        <GovukHeading as="h2" size="m">
          Nature of processing
        </GovukHeading>
        <GovukList type="bullet">
          <GovukListItem>
            <strong>Collection:</strong> When we ask you for information, we
            will keep to the law, including the Data Protection Act 2018 and UK
            General Data Protection Regulation. Personal Data will be gathered
            during user research and engagement activities, Local Transcribe as
            a live product and Local Transcribe evaluation.
          </GovukListItem>
          <GovukListItem>
            <strong>Storage:</strong>
            <GovukList type="bullet">
              <GovukListItem>
                All Personal Data will be securely stored. Personal Data from
                activities between MHCLG and Local Transcribe Partner Councils
                during user research and engagement activities, Local Transcribe
                as a live product and Local Transcribe evaluation will be stored
                in line with GDPR, ICO guidance, user research ethics, and
                governance.
              </GovukListItem>
              <GovukListItem>
                Your Personal Data from user research and engagement activities
                will be stored in the third-party software used by the MHCLG
                Department, such as SharePoint.
              </GovukListItem>
              <GovukListItem>
                Any artefacts with Personally Identifiable Information from user
                research and engagement activities between frontline workers and
                team members from Local Transcribe such as recordings of
                meetings, will be stored in a password protected folder.
              </GovukListItem>
              <GovukListItem>
                Information will be aggregated and anonymised and outcome
                artefacts will have Personally Identifiable Information removed.
              </GovukListItem>
              <GovukListItem>
                Personal Data within Local Transcribe will be securely stored.
              </GovukListItem>
              <GovukListItem>
                Our technical team will take protective measures to ensure the
                appropriate technical and organisational measures are in place
                which may include pseudonymising and encrypting Personal Data,
                ensuring confidentiality, integrity, availability and resilience
                of systems and services, ensuring that availability of and
                access to Personal Data can be restored in a timely manner after
                an incident, and regularly assessing and evaluating the
                effectiveness of such measures.
              </GovukListItem>
            </GovukList>
          </GovukListItem>
          <GovukListItem>
            <strong>Organisation:</strong> Personal Data will be saved in a
            structured and organised manner to aid retrieval and analysis.
          </GovukListItem>
          <GovukListItem>
            <strong>Use:</strong> Personal Data from engagement activities will
            be used to understand the workflow and activities of Local
            Transcribe Partner Councils personnel, local council employees, team
            managers, and frontline workers. This will inform how to adapt,
            design, build and deliver Local Transcribe to serve local councils
            and the work of their personnel, local council employees, team
            managers, frontline workers as well as overall service delivery for
            service users. Audio data and data from case management systems or
            surveys shared by Local Transcribe Partner Councils for the purpose
            of testing and evaluation of Local Transcribe will be used to assess
            and optimise Local Transcribe. Audio data shared by Local Transcribe
            Partner Councils personnel, local council employees, team managers,
            and frontline workers, for the purpose of transcription within Local
            Transcribe will be processed for the purpose of transcription and
            generating summaries within Local Transcribe.
          </GovukListItem>
        </GovukList>

        <GovukHeading as="h2" size="m">
          What Personal Data is being collected
        </GovukHeading>
        <GovukList type="bullet">
          <GovukListItem>
            The following Personal Data from local council personnel, local
            council employees, team managers, frontline workers is being
            collected for the described purpose:
            <GovukList type="bullet">
              <GovukListItem>Full name</GovukListItem>
              <GovukListItem>Role</GovukListItem>
              <GovukListItem>Local authority</GovukListItem>
              <GovukListItem>Local council department</GovukListItem>
              <GovukListItem>Email address</GovukListItem>
            </GovukList>
          </GovukListItem>
          <GovukListItem>
            Personal Data within Audio Data
            <GovukList type="bullet">
              <GovukListItem>
                Audio data shared by Local Transcribe Partner Councils
                personnel, local council employees, team managers, frontline
                workers when they use Local Transcribe
              </GovukListItem>
              <GovukListItem>
                Audio data shared by Local Transcribe Partner Councils when they
                agree to share this data, for the purpose of Local Transcribe
                evaluation
              </GovukListItem>
              <GovukListItem>
                This includes audio data from meetings between frontline workers
                and service users, and for the avoidance of doubt this means
                that audio data may contain, or will contain Personal Data from
                service users and depending on what’s discussed during meetings
                between frontline workers and service users the audio data may
                contain special category and criminal offence data
              </GovukListItem>
            </GovukList>
          </GovukListItem>
          <GovukListItem>
            Personal Data within case management system data and survey data
            <GovukList type="bullet">
              <GovukListItem>
                Data from case management systems or surveys shared by Local
                Transcribe Partner Councils when they agree to share this data,
                for the purpose of Local Transcribe evaluation
              </GovukListItem>
              <GovukListItem>
                This may include case note data from case management systems,
                and for the avoidance of doubt this means that case management
                data may contain, or will contain personal data from service
                users
              </GovukListItem>
            </GovukList>
          </GovukListItem>
          <GovukListItem>
            Local Transcribe Partner Councils undertakes to comply with the
            applicable Data Protection Legislation in respect of their
            processing of Personal Data as a Joint Controller of data as part of
            their delivery of a service to service uses.
          </GovukListItem>
        </GovukList>

        <GovukHeading as="h2" size="m">
          What non-Personal Data is being collected
        </GovukHeading>
        <GovukList type="bullet">
          <GovukListItem>
            Information shared by Local Transcribe Partner Councils as part of
            user research and engagement activities e.g. ways of working, end to
            end activities carried out by frontline workers for service delivery
          </GovukListItem>
        </GovukList>

        <GovukHeading as="h2" size="m">
          Special category and criminal offence data
        </GovukHeading>
        <GovukList type="bullet">
          <GovukListItem>
            Any special category and criminal offence data shared by Local
            Transcribe Partner Councils personnel, local council employees, team
            managers, frontline workers, will be the responsibility of Local
            Transcribe Partner Councils to handle in line with GDPR, and ICO
            guidance.
          </GovukListItem>
          <GovukListItem>
            Data within Local Transcribe, shared by the local authority, will be
            processed by Local Transcribe in line with GDPR, and ICO guidance.
          </GovukListItem>
          <GovukListItem>
            Both MHCLG and Local Transcribe Partner Councils undertake to comply
            with the applicable Data Protection Legislation in respect of their
            processing of Personal Data as a Joint Controller.
          </GovukListItem>
          <GovukListItem>
            Both MHCLG and Local Transcribe Partner Councils remain responsible
            as Joint Controllers for instructing their own Data Processors to
            comply with the applicable Data Protection Legislation in respect of
            their processing of Personal Data.
          </GovukListItem>
        </GovukList>

        <GovukHeading as="h2" size="m">
          Lawful basis for processing the data
        </GovukHeading>
        <GovukList type="bullet">
          <GovukListItem>
            Data protection legislation sets out when we are lawfully allowed to
            process your data.
          </GovukListItem>
          <GovukListItem>
            The lawful basis for Local Transcribe is Article 6(1)(e) of the UK
            General Data Protection Regulation (UK GDPR) – Public Task.
          </GovukListItem>
          <GovukListItem>
            Public task means we are processing your Personal Data because it is
            necessary for us to carry out our official functions in the public
            interest.
          </GovukListItem>
          <GovukListItem>
            We will only use your Personal Data for the purposes of user
            research and engagement activities, Local Transcribe as a live
            product, Local Transcribe evaluation, and in line with our legal
            responsibilities under data protection law.
          </GovukListItem>
        </GovukList>

        <GovukHeading as="h2" size="m">
          Privacy Notice
        </GovukHeading>
        <p className="govuk-body">
          This privacy notice explains how and why we use your personal
          information. It sets out what data we collect, what we use it for, how
          long we keep it, and what your rights are.
        </p>
        <p className="govuk-body">
          This privacy notice is authored by MHCLG and is not intended to
          replace each local authority’s own service-specific privacy
          information. Councils remain responsible for determining the
          appropriate usage of Local Transcribe in their own service delivery
          and for ensuring service users are provided with appropriate
          transparency information.
        </p>

        <GovukHeading as="h2" size="m">
          With whom we will be sharing the data
        </GovukHeading>
        <GovukList type="bullet">
          <GovukListItem>
            The data will be able to be accessed by those employed by MHCLG, and
            the Local Transcribe team.
          </GovukListItem>
          <GovukListItem>
            This includes third-party contractors from Softwire and Sparta
            Global, which support the delivery of Local Transcribe process
            personal data on MHCLG’s instruction.
          </GovukListItem>
          <GovukListItem>
            Audio data and associated transcripts may also be processed by
            service providers acting on MHCLG’s instructions for secure hosting,
            speech-to-text transcription, summarisation, product analytics,
            performance monitoring and error tracking.
          </GovukListItem>
        </GovukList>

        <GovukHeading as="h2" size="m">
          Duration of the processing
        </GovukHeading>
        <p className="govuk-body">
          The processing of Personal Data begins from the start of the
          activities of Local Transcribe Partner Councils and MHCLG during user
          research and engagement activities, Local Transcribe as a live product
          and Local Transcribe evaluation.
        </p>
        <p className="govuk-body">
          Processing of Personal Data from audio data begins when personnel from
          Local Transcribe Partner Councils, local council employees, team
          managers and frontline workers use Local Transcribe to record meetings
          or upload audio data to Local Transcribe or share audio data with
          MHCLG for testing purposes and evaluation of Local Transcribe, during
          the activities of Local Transcribe as a live product and Local
          Transcribe evaluation.
        </p>
        <p className="govuk-body">
          Processing of Personal Data from case management systems or surveys
          under this DSA begins when personnel from Local Transcribe Partner
          Councils, local council employees, team managers and frontline workers
          share case management or survey data with MHCLG for testing purposes
          and evaluation of Local Transcribe, during the activities of Local
          Transcribe evaluation.
        </p>
        <p className="govuk-body">
          Processing of Personal Data shall continue for the duration of Local
          Transcribe Partner Councils, participation in user research and
          engagement activities, Local Transcribe as a live product and Local
          Transcribe evaluation, and only for so long as such processing remains
          necessary and proportionate to the purposes set out in this privacy
          notice.
        </p>
        <p className="govuk-body">
          Processing of Personal Data shall cease when a Local Transcribe
          Partner Council ceases participation in user research and engagement
          activities, when Local Transcribe Partner Councils requests to have
          their data deleted, when a service user requests to have their data
          deleted, or when 6 months has elapsed from the start of data
          processing.
        </p>
        <p className="govuk-body">
          Processing of Personal Data from audio data ceases based on the
          deletion date set within Local Transcribe by Local Transcribe Partner
          Councils personnel, local council employees, team managers, and
          frontline worker. This defaults to 7 days but is configurable between
          1 and 30 days by the user. Alternatively, processing will cease when a
          Local Transcribe Partner Council requests to have their audio data
          deleted, or if a service user requests to have their audio data
          deleted.
        </p>
        <p className="govuk-body">
          Processing of Personal Data from audio data for Local Transcribe
          evaluation continues for 12 months. Alternatively, processing will
          cease when a Local Transcribe Partner Council requests to have their
          audio data deleted.
        </p>
        <p className="govuk-body">
          Processing of Personal Data in event data and logs derived from audio
          data ceases after 90 days.
        </p>
        <p className="govuk-body">
          Processing of Personal Data in metrics and analytics data ceases after
          14 months or when a Local Transcribe Partner Council requests to have
          their audio data deleted.
        </p>
        <p className="govuk-body">
          Processing of Personal Data from case management systems or surveys
          ceases after 14 months or when a Local Transcribe Partner Council
          requests to have their audio data deleted.
        </p>

        <GovukHeading as="h2" size="m">
          Your rights, e.g. access, rectification, erasure
        </GovukHeading>
        <p className="govuk-body">
          The data we are collecting is your Personal Data, and you have rights
          that affect what happens to it. You have the right to:
        </p>
        <GovukList type="bullet">
          <GovukListItem>
            know that we are using your Personal Data
          </GovukListItem>
          <GovukListItem>see what data we have about you</GovukListItem>
          <GovukListItem>
            ask to have your data corrected, and to ask how we check the
            information we hold is accurate
          </GovukListItem>
          <GovukListItem>
            ask to restrict how we use personal data or object to certain
            processing
          </GovukListItem>
          <GovukListItem>ask for your data to be deleted</GovukListItem>
          <GovukListItem>complain to the ICO (see below)</GovukListItem>
        </GovukList>
        <p className="govuk-body">
          You may ask us to delete your personal information or stop using it.
          We will consider your request in accordance with data protection law.
          These rights do not apply in every circumstance, and we may need to
          retain some information where there is a lawful reason to do so. We
          will explain the outcome of your request and the reasons for our
          decision.
        </p>

        <GovukHeading as="h2" size="m">
          Sending data overseas
        </GovukHeading>
        <p className="govuk-body">
          Data will be transferred to the European Economic Area (Sweden and
          Germany) for processing by speech-to-text and LLM services, product
          analytics and performance monitoring and error tracking. No data is
          stored outside of the UK by speech-to-text and LLM services and no
          data is retained or used for AI training. Data is stored in the EEA
          for product analytics and performance monitoring and error tracking
          only.
        </p>

        <GovukHeading as="h2" size="m">
          Automated decision making
        </GovukHeading>
        <p className="govuk-body">
          No automated decision making will take place using the data collected.
        </p>

        <GovukHeading as="h2" size="m">
          Complaints
        </GovukHeading>
        <p className="govuk-body">
          If you are unhappy with the way the MHCLG Department has acted, you
          can make a complaint.
        </p>
        <GovukList type="bullet">
          <GovukListItem>
            The Local Transcribe team can be contacted at{' '}
            <a className="govuk-link" href="mailto:localai@communities.gov.uk">
              localai@communities.gov.uk
            </a>
          </GovukListItem>
          <GovukListItem>
            The Data Protection Officer at MHCLG can be contacted at{' '}
            <a
              className="govuk-link"
              href="mailto:dataprotection@communities.gov.uk"
            >
              dataprotection@communities.gov.uk
            </a>
          </GovukListItem>
          <GovukListItem>
            If you want to make a Subject Access Request, another request in
            relation to your rights, or if you are not happy with how we are
            using your Personal Data, you can contact{' '}
            <a
              className="govuk-link"
              href="mailto:dataprotection@communities.gov.uk"
            >
              dataprotection@communities.gov.uk
            </a>
          </GovukListItem>
        </GovukList>
        <p className="govuk-body">
          If you are still not happy, or for independent advice about data
          protection, privacy and data sharing, you can contact:
        </p>
        <p className="govuk-body">
          The Information Commissioner’s Office
          <br />
          Wycliffe House
          <br />
          Water Lane
          <br />
          Wilmslow, Cheshire,
          <br />
          SK9 5AF
        </p>
        <p className="govuk-body">
          Telephone: 0303 123 1113 or 01625 545 745
          <br />
          <a className="govuk-link" href="https://ico.org.uk/">
            https://ico.org.uk/
          </a>
        </p>
      </div>
    </div>
  )
}

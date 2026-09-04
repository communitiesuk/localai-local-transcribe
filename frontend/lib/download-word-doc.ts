import { citationRegexWithSpace } from '@/lib/citationRegex'
import { DialogueEntry } from '@/lib/client'
import { saveAs } from 'file-saver'
import { asBlob } from 'html-docx-js-typescript'

function getDocumentStyles(): string {
  return `
    <style>
      body {
        white-space: pre-wrap;
        font-family: Helvetica, Arial, sans-serif;
        font-size: 11pt;
      }
      p {
        margin: 0;
        padding: 0;
        line-height: 1.15;
      }
      pre, code {
        font-family: 'Courier New', Courier, monospace;
      }
      blockquote {
        margin-left: 20px;
        padding-left: 10px;
        border-left: 3px solid #ccc;
      }
    </style>
  `
}

export function formatTranscript(transcript: DialogueEntry[]): string {
  return transcript
    .map(
      (entry) =>
        `<p><strong>${entry.speaker}</strong>: ${entry.text}</p><p>&nbsp;</p>`
    )
    .join('\n')
}

export function preprocessHtml(
  html: string,
  transcript: DialogueEntry[]
): string {
  // Handle line breaks and empty paragraphs
  const processedHtml = html
    .replace(/<br\s*\/?>/gi, '</p><p>')
    .replace(/<p>\s*<\/p>/gi, '<p>&nbsp;</p>')

  const formattedTranscript = formatTranscript(transcript)

  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<?mso-application progid="Word.Document"?>
<html xmlns:w="urn:schemas-microsoft-com:office:word"
      xmlns:m="http://schemas.microsoft.com/office/2004/12/omml"
      xmlns:v="urn:schemas-microsoft-com:vml"
      xmlns:o="urn:schemas-microsoft-com:office:office">
    <head>
      ${getDocumentStyles()}
      <xml>
        <w:WordDocument>
          <w:View>Print</w:View>
          <w:Zoom>100</w:Zoom>
          <w:DoNotOptimizeForBrowser/>
        </w:WordDocument>
      </xml>
      <style>
        @page Section1 {
          size: 8.5in 11.0in;
          margin: 1.0in 1.0in 1.0in 1.0in;
          mso-header-margin: .5in;
          mso-footer-margin: .5in;
          mso-footer: f1;
        }
        div.Section1 { page: Section1; }
        div.f1 {
          mso-element: footer;
          margin: 0in 0in 0in 0in;
          font-size: 11pt;
        }
        /* Hide footer in browser but not in Word */
        @media screen {
          div.f1 {
            display: none;
          }
        }
      </style>
    </head>
    <body>
      <div class="Section1">
        ${processedHtml}
        <p>&nbsp;</p>
        <p><strong>Meeting Transcript:</strong></p>
        <p>&nbsp;</p>
        ${formattedTranscript}
      </div>
      <div class="f1">
        <p style="text-align:center">
          <span style="font-family: Arial;">OFFICIAL SENSITIVE</span>
        </p>
      </div>
    </body>
</html>`
}

async function getNewFileHandle(
  fileName: string
): Promise<FileSystemFileHandle | null> {
  const options = {
    suggestedName: fileName,
    types: [
      {
        description: 'Word document',
        accept: {
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            ['.docx'],
        },
      },
    ],
  }

  if (!window.showSaveFilePicker) {
    return null
  }

  return await window.showSaveFilePicker(options)
}

async function getNewFileHandleOrAbort(
  fileName: string
): Promise<FileSystemFileHandle | null | undefined> {
  // cancelling FileSave causes an AbortError so catch that here
  try {
    return await getNewFileHandle(fileName)
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      return undefined
    }

    throw error
  }
}

async function wordBlobToFile(
  blob: Blob,
  fileName: string,
  fileHandle: FileSystemFileHandle | null | undefined
) {
  if (fileHandle === undefined) {
    // user cancelled download
    return false
  }

  if (fileHandle === null) {
    // fallback as FilePicker is experimental so may be null
    saveAs(blob, fileName)
    return true
  }

  const writable = await fileHandle.createWritable()
  await writable.write(blob)
  await writable.close()
  return true
}

export async function downloadTranscriptDoc(
  transcript: DialogueEntry[],
  fileName: string = 'transcript.docx'
): Promise<boolean> {
  const fileHandle = await getNewFileHandleOrAbort(fileName)

  const html = `<!DOCTYPE html><html><head>${getDocumentStyles()}</head><body>${formatTranscript(transcript)}</body></html>`
  const result = await asBlob(html)
  const blob = result instanceof Blob ? result : new Blob([result as BlobPart])

  return await wordBlobToFile(blob, fileName, fileHandle)
}

async function convertHTMLToWordAndDownload(
  htmlContent: string,
  transcript: DialogueEntry[],
  fileName: string = 'ai-minutes.docx'
): Promise<boolean> {
  const fileHandle = await getNewFileHandleOrAbort(fileName)

  const processedHtml = preprocessHtml(htmlContent, transcript)
  const result = await asBlob(processedHtml)
  const blob = result instanceof Blob ? result : new Blob([result as BlobPart])

  return await wordBlobToFile(blob, fileName, fileHandle)
}

async function convertAIMinutesToWordDoc(
  html: string,
  transcript: DialogueEntry[],
  fileName: string = 'document.docx'
): Promise<boolean> {
  const cleanedHTML = html.replace(citationRegexWithSpace, '')
  return await convertHTMLToWordAndDownload(cleanedHTML, transcript, fileName)
}

export default convertAIMinutesToWordDoc

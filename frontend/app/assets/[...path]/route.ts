import { NextRequest, NextResponse } from 'next/server'
import path from 'path'
import fs from 'fs'

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  // Extract the full path from the catch-all segments
  const assetPath = params.path.join('/')

  // Resolve the absolute path to the asset in node_modules
  const filePath = path.join(
    process.cwd(),
    'node_modules/govuk-frontend/dist/govuk/assets',
    assetPath
  )

  // Security check: Ensure the resolved path is still within the expected assets directory
  const assetsRoot = path.resolve(
    process.cwd(),
    'node_modules/govuk-frontend/dist/govuk/assets'
  )
  const absoluteFilePath = path.resolve(filePath)

  if (!absoluteFilePath.startsWith(assetsRoot)) {
    return new NextResponse('Forbidden', { status: 403 })
  }

  if (fs.existsSync(absoluteFilePath) && fs.lstatSync(absoluteFilePath).isFile()) {
    const fileBuffer = fs.readFileSync(absoluteFilePath)
    const extension = path.extname(absoluteFilePath).toLowerCase()

    const contentTypes: Record<string, string> = {
      '.woff': 'font/woff',
      '.woff2': 'font/woff2',
      '.svg': 'image/svg+xml',
      '.png': 'image/png',
      '.ico': 'image/x-icon',
      '.json': 'application/json',
    }

    const contentType = contentTypes[extension] || 'application/octet-stream'

    return new NextResponse(fileBuffer, {
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=31536000, immutable',
      },
    })
  }

  return new NextResponse('Asset not found', { status: 404 })
}

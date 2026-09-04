# ADR-029: Client-side Audio Protection

## Status

Proposed

Date of decision: {yyyy-MM-dd}

## Context and Problem Statement

As currently implemented, recordings (from microphone or system audio) are held in the browser's IndexedDB
whilst ongoing. When the recording is complete, if the user is online then the audio is uploaded to S3 and
deleted locally; if offline (or the upload fails), the audio file is held as an "offline recording"
indefinitely, until the user either manually triggers an upload or deletion. This presents an increased
data risk.

How should we protect potentially sensitive audio recorded by Local Transcribe?

## Considered Options

* In-app offline recording expiry
* Per-user asymmetric encryption
* Hybrid encryption, server-held keys, local audio decryption
* Hybrid encryption, server-held keys, server audio decryption
* Hybrid encryption, WebAuthn-held keys
* Per-recording symmetric encryption
* Per-recording passphrases

Note that it is possible to combine some options, but each option is considered independently here.

## Decision Outcome

Hybrid encryption, server-held keys, local audio decryption, because this encrypts all audio locally
only at the cost of preventing offline playback (which we do not expect to be commonplace).

## Pros and Cons of the Options

### In-app offline recording expiry

The client-side application deletes 'expired' offline recordings (e.g. older than one week), both
at application launch and on a regular basis thereafter (e.g. every 6 hours). Optionally, request
user permissions before deleting and/or allow the user to extend expiration dates.

* Good, because it typically limits the amount of time audio date remains on a client device.
* Bad, because it’s not guaranteed: the user may never open Local Transcribe again, so the expiry deletion may not
  occur.
* Neutral, because it does not affect how easy/hard it is to access locally held data while it still exists.

### Per-user asymmetric encryption

For each user, generate a public/private key pair, expose the public key and keep the private key on the server.
Request the user's public key on logging in (and/or store it locally) and encrypt audio using that key. Decrypt the
audio on the server-side.

* Good, because it encrypts locally held data. 
* Good, because encryption works whether the user is offline or online. 
* Bad, because users cannot listen to their offline recordings without first uploading them (i.e. whilst online). 
* Bad, because encrypting the newly appended audio blob on every storage event is expensive, especially for long recordings. 

### Hybrid encryption, server-held keys, local audio decryption

Generate per-user public/private key pairs, as above. For each recording, create a client-side symmetric key and use it
to encrypt stored audio chunks. Encrypt ("wrap") the symmetric key via the user's public key (retrieved at log in /
stored locally, as above) and store the wrapped key in IndexedDB with the audio.

At upload or playback time, request the unwrapped symmetric key from the server (the client sends the wrapped key, the
server decrypts it using the private key and sends the unwrapped key back), then decrypt all the audio chunks and stitch
them together.

* Good, because it encrypts locally held data. 
* Good, because encryption works whether the user is offline or online. 
* Bad, because users cannot listen to their recordings without being online (to get the decrypted symmetric key). 
* Good, because symmetric de/encryption is cheaper, and can be performed per chunk of audio, rather than per entire
  blob.

### Hybrid encryption, server-held keys, server audio decryption

As above, but instead of the client requesting the decrypted symmetric key, the client sends the wrapped key and the
encrypted chunks, and the server decrypts and stitches the chunks together. 

This has the same properties as above, but:

* Bad, because users cannot listen to recordings without first uploading them.
* Bad, because the computationally expensive decryption operations are concentrated on Local Transcribe infrastructure,
  rather than distributed across many clients.
* Good, because the symmetric key exposure is reduced. 

### Hybrid encryption, WebAuthn-held keys

WebAuthn PRF is a pseudorandom function provided by the browser. Conceptually, it takes both a secret and a salt and
returns a deterministic but pseudorandom result. The salt is provided by the JS application, but the secret is provided
by the WebAuthn authenticator – this varies by browser and platform, but the important point is that the secret itself
is not available to JS, and the WebAuthn vault can only be opened via user interaction (e.g. Touch ID, Face ID, Windows
Hello, device PIN). 

For each recording, using WebAuthn PRF and a random salt to generate a (symmetric) key encryption key (KEK). Generate a
(symmetric) data encryption key (DEK) in the JS. Encrypt the audio with the DEK. Encrypt ("wrap") the DEK with the KEK.
Store the PRF salt, wrapped KEK, and audio in IndexedDB. 

At decryption time – either upload or playback – use WebAuthn PRF and the stored salt to regenerate the KEK, decrypt the
DEK, then decrypt the audio chunks and stitch them together.

To mitigate XSS attack risks, the audio recording, encryption, storage, decryption, playback (via iframe), and upload JS
could be moved to a ‘vault’ subdomain, which serves no user-generated content and has a tight CSP. 

* Good, because it encrypts locally held data.
* Good, because encryption works whether the user is offline or online.
* Good, because the user can decrypt offline (to listen to recordings).
* Good, because symmetric de/encryption is cheaper, and can be performed per chunk of audio, rather than per entire
  blob.
* Neutral, because XSS JS injected into the vault subdomain could still try to monitor for WebAuthn to be opened and
  then decrypt audio – but this is a very small attack surface, so requires a very sophisticated attack.
* Bad, because browser / OS support is patchy - far from universal, even amongst developer team devices.
* Bad, because users may be unfamiliar with the WebAuthn browser interaction.
* Bad, because audio playback in an iframe may have negative accessibility impact and/or require us to build our own
  player, rather than use the browser-native one.

### Per-recording symmetric encryption

For each recording, generate a symmetric encryption key and store it in RDS. Keep the key in memory client-side during
recording to encrypt the audio chunks. Request the key at upload / playback time (if needed) to decrypt the chunks and
stitch them together.

* Good, because it encrypts locally held data.
* Bad, because encryption is only possible if the user is online when recording starts.
* Bad, because the user cannot listen to their recordings without being online (or still having the key in memory).
* Good, because symmetric de/encryption is cheaper, and can be performed per chunk of audio rather than per entire
  blob.

### Per-recording passphrases

When starting a recording, ask the user for a password and use that as a symmetric encryption key (or derive the key
from it). Never store the password/key. Request the password from the user at upload / playback time to decryption and
stitch together the audio.

* Good, because it encrypts locally held data.
* Good, because encryption works whether the user if offline or online.
* Good, because the user can decrypt offline (to listen to recordings).
* Good, because symmetric de/encryption is cheaper, and can be performed per chunk of audio rather than per entire
  blob.
* Bad, because users are regularly asked for passwords and must manage those passwords themselves.
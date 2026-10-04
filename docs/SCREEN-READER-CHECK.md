# Screen-reader check (Phase 2 accessibility)

A person with VoiceOver on a Mac, about 30 to 45 minutes. The bots have already passed the
automated checks (axe-core at zero for labels, contrast and colour-only links, keyboard
navigation, 200 percent zoom). This is the part only a person can judge: does it make sense
when you can only hear it?

Use **Safari**, which VoiceOver works with best. Use **qa2** (https://qa2.coil.legal), the
QA Bot 2 firm, with the qa2 owner login. Name anything you create `QA2 SR 20261004`.

## Setup (2 minutes)

- Turn VoiceOver on and off with **Cmd + F5**.
- **VO** means **Control + Option** held together.
- Read the next item: **VO + Right arrow**. Previous: **VO + Left arrow**.
- Click the item VoiceOver is on: **VO + Space**.
- The rotor (a list of headings, links, form fields on the page): **VO + U**, then Left or
  Right arrow to switch lists, Up or Down to move, Enter to jump.
- Tab and Shift+Tab move between links, buttons and fields, as usual.

For each step, write **OK** or what went wrong in a sentence: what you heard, and what you
expected to hear.

## Steps

| # | Do this | Listen for | Result |
|---|---|---|---|
| 1 | Signed out, open https://qa2.coil.legal/intake/form. Open the rotor (VO + U) and look at Headings, then Form Controls. | One clear page heading. Every field listed by its label ("Your name", "Email", and so on), none as just "edit text". | |
| 2 | Tab through the form to the submit button without filling anything, and press it. | The "Please tell us your name." message is read out, or is easy to find right after. | |
| 3 | Fill name `QA2 SR 20261004` and submit. | The thank-you page announces itself. | |
| 4 | Open https://qa2.coil.legal/login and sign in using only the keyboard. | Email and password fields are named; a wrong password message is read. | |
| 5 | On the dashboard, open the rotor: Headings, then Landmarks (if offered). | Headings that describe the cards; a way to jump to the main content and to the sidebar. | |
| 6 | Tab through the sidebar. | Each link says where it goes. Focus is easy to follow. | |
| 7 | Open Contacts, then New contact. Fill a person `QA2 SR 20261004` and save. | Every field named; "Contact created." is read or easy to find. | |
| 8 | Open a matter (any QA2 matter), then move through its tabs. | The tabs are announced as tabs (or clear links), and you can tell which one is selected. | |
| 9 | On that matter's Documents tab, find the upload control. | It is named ("Upload a file, 25 MB max"), and the "Share to client portal" checkbox says what it does. | |
| 10 | Calendar: open New event, fill a title and time, save. | Date and time fields are usable and named; "Event added." is read. | |
| 11 | Conflict check: type `QA2 SR 20261004` in the names box and run it. | The results are understandable: how many hits, what each hit is, and its status. | |
| 12 | In https://qa2.coil.legal/qa-mail/ (signed in as owner), find a portal sign-in email for a QA2 client and open the link in a private window. | The portal home reads sensibly: who you are, your matters, documents, messages. | |
| 13 | In the portal, send a message `QA2 SR 20261004`. | The message box is named; "Your message was sent." is read. | |
| 14 | Anywhere: any button that is only an icon (an "x", a pencil, a bin). | Every icon button has a spoken name. Note any that are silent or say only "button". | |

## When you are done

Send the table to Claude Code, or paste it as a comment on Coil-Legal/coil issue #89
starting `[Ian]`. Anything marked wrong becomes a `QA2:` issue for the loop to fix. If
steps 1 to 14 are OK, the Phase 2 accessibility row can be signed off.

Delete the `QA2 SR 20261004` contact and event afterwards, or leave them; they are test data.

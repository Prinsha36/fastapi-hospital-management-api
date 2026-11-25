# Design Gaps

Keep an item open until its acceptance criteria are met and verified. When closing an item, add a short note describing what changed and how it was checked. Record partial progress under the open item.

## High priority

- [ ] **Protect patient records.** Require staff authentication on sensitive patient, appointment, and emergency read routes, including related-record endpoints. The browser should prompt users to sign in before loading those records. Verify anonymous API requests are rejected, authorized staff can still work, and signing out clears sensitive data from the view.
- [ ] **Keep the emergency queue current.** Refresh the queue automatically while it is visible, show when it was last updated, and indicate when a refresh fails. Verify that changes made in another session appear without manual refresh.
- [ ] **Make emergency actions accessible on phones.** Keep the patient, triage priority, and relevant action visible without horizontal scrolling. Verify assignment and closure on a narrow viewport using touch and keyboard navigation.

## Medium priority

- [ ] **Make patient and doctor pickers searchable.** Fetch paginated search results instead of loading entire directories. Show enough context to distinguish duplicate names. Verify that booking works with records beyond the first page and that existing selections remain visible when editing.
- [ ] **Make the dashboard reliable when requests fail.** Load panels independently and use an API summary for exact counts. Verify that one failed request leaves the other panels usable and that counts remain correct above 100 records.
- [ ] **Identify records in delete confirmations.** Show the record name or meaningful case identifier and describe any related records that will be deleted. Verify that the dialog identifies the selected record and that cancelling leaves it intact.

# Proposed Breakdown and Workaround Consolidation

This document proposes a consolidated taxonomy for the `breakdown` and `workaround` fields based on the four induction runs. It is for review only and has not yet been assigned against the corpus.

## breakdown

**Search Indexing & Processing Delays**: Temporarily unavailable search results because Google Photos has not yet processed, indexed, or recognized newly uploaded, backed up, or modified content.
*Merged from*: Indexing Delays (run_1), Indexing & Processing Delays (run_2, run_4), Search Not Indexing (run_3)
*Example phrases*: "Photo had not yet been indexed by Google Photos"; "Search performed too soon after backup, before indexing completed"; "Processing delay while Google Photos indexes content"

**Backup & Sync Failures**: Photos fail to appear in Google Photos because they were not properly uploaded, synced, or backed up to the cloud service, or backup configuration is incomplete.
*Merged from*: Sync/Upload Failures (run_1), Sync & Backup Failure (run_2), Upload/Sync Not Complete (run_3), Backup & Sync Problems (run_4)
*Example phrases*: "Photo not uploading or syncing"; "Backup not completing properly"; "Photos not appearing despite being saved to Drive"

**Face Recognition Failure**: Facial recognition and face-based search is not working correctly, including failure to detect new faces, incorrect face grouping, or inability to search by person's name.
*Merged from*: Facial Recognition Issues (run_1), Face Recognition Failure (run_2, run_3), Face Detection & Recognition Issues (run_4)
*Example phrases*: "Face detection not recognizing new faces"; "Me identifier assigned to wrong person"; "Face search fails to retrieve photos of specific people"

**Search Quality Degradation**: Search functionality has become less effective over time, returning fewer relevant results, more irrelevant results, or producing inconsistent output compared to previous performance.
*Merged from*: Low Precision Search Results (run_1), Low Recall Search Results (run_1), Search Quality Degradation (run_2), AI Search Degradation (run_3), Search Algorithm Degradation (run_4)
*Example phrases*: "Search returns mostly irrelevant results"; "Finds only a small cluster of matching photos instead of most results"; "Search quality has declined significantly"

**AI Search Integration Issues**: Problems introduced or caused by the shift to Gemini AI-based search, including reduced keyword matching, poor natural language understanding, or feature removal.
*Merged from*: Gemini AI Integration Issues (run_1), AI Search Limitations (run_2), Gemini AI Search Issues (run_4)
*Example phrases*: "Gemini AI search replaced keyword search"; "AI fails to understand natural language queries"; "Classic keyword search no longer works"

**Keyword & Description Search Failure**: Text-based keyword, tag, or description search fails to match relevant photos despite the search terms being present in image content, metadata, or manually added descriptions.
*Merged from*: Keyword Indexing Degradation (run_1), Text & OCR Search Failure (run_2), Keyword Search Not Matching (run_3), Keyword & Description Search Failures (run_4)
*Example phrases*: "Search stopped recognizing keywords in Info field"; "Keyword searches return zero results"; "Tagged descriptions no longer match in search"

**OCR & Text-in-Image Search Failure**: Optical character recognition and text-in-image search is not working or has become inconsistent, failing to match visible text within photos.
*Merged from*: OCR/Text Recognition Failure (run_1), Text/OCR Search Failing (run_3), OCR & Text Search Failures (run_4)
*Example phrases*: "OCR failed to match visible text in image"; "Text search no longer finds photos with specific words"; "Text recognition in screenshots inconsistent"

**Date Search Issues**: Searching, filtering, or sorting by date is not working correctly, returning all photos from a date instead of specific ones, or failing to filter by date range.
*Merged from*: Date Search Issues (run_1), Date Search Issues (run_2), Date Search Malfunction (run_3), Date-Based Search Problems (run_4)
*Example phrases*: "Date search returns random unrelated results"; "All photos from that day returned instead of specific photo"; "App update broke date filtering"

**Filename Search Malfunction**: Search by filename is not supported, does not match filenames accurately, or over-matches on partial filename components.
*Merged from*: Filename Search Limitations (run_1), Filename Search Issues (run_2), Filename Search Not Working (run_3), Filename Search Malfunction (run_4)
*Example phrases*: "Search matches only the year portion of filename"; "Filename search not supported"; "Over-matches on partial tokens instead of exact filename"

**Location Search Limitations**: Location-based search or filtering is unavailable, incomplete, or unable to match unmapped or remote locations.
*Merged from*: Location Search Issues (run_1), Location Search Limitations (run_2), Location Search Issue (run_3), Location-Based Search Limitations (run_4)
*Example phrases*: "Remote location has no named place to search"; "Location search returns incomplete results"; "Map view unavailable on web version"

**Search Term Filtering & Censorship**: Specific search terms are blocked, filtered, or censored by Google Photos, preventing normal searches even for non-NSFW content.
*Merged from*: Content Filtering/Censorship (run_1), Banned Search Terms (run_2), Search Term Blocked (run_3), Search Term Filtering & Censorship (run_4)
*Example phrases*: "Search term tattoo appears blocked"; "Searches for women return zero results"; "Certain words trigger filtering preventing search"

**Album Search & Navigation Issues**: Albums, collections, or grouped content cannot be found through search, are not indexed by title, or lack searchable organization.
*Merged from*: Search Feature Removal (run_1), Album Search & Access (run_2), Album/Collection Not Found (run_3), Album Search & Navigation Failures (run_4)
*Example phrases*: "No search function for album titles"; "Album disappeared from normal interface"; "Searching album name returns no results"

**Metadata Mismatch & Sorting Issues**: Photos are not searchable or correctly sorted because their metadata (date, location, EXIF) is incorrect, not respected, or misaligned.
*Merged from*: Metadata Mismatch (run_1), Metadata & Sorting Problems (run_2), Metadata/Sorting Issue (run_3), Metadata & Sorting Issues (run_4)
*Example phrases*: "EXIF date metadata not respected during sorting"; "Photos sorted by upload date instead of date taken"; "Camera location metadata ignored"

**Edited Content Display Issues**: Edited versions of photos or modified metadata do not appear in search, display results, or UI correctly, or the app reverts to original images.
*Merged from*: Edited/Modified Content (run_1), Editing & Display Issues (run_2)
*Example phrases*: "Edited file not displayed in search"; "Saved edit reverts to original image"; "Modified photo missing from Recently Added"

**Cross-Platform & Device Inconsistency**: Search or display behavior differs between different versions, platforms, or devices (mobile app vs. web, Android vs. iOS).
*Merged from*: Cross-Platform Inconsistency (run_1), Search Result Inconsistency (run_2), Inconsistent Cross-Platform Search (run_3), Platform Inconsistencies (run_4)
*Example phrases*: "Mobile app returns no results while web browser finds photos"; "Search results differ between Pixel and PC"; "Feature inconsistent between Android and iOS"

**Content Recognition & Semantic Search Failure**: Google Photos' AI fails to recognize or match descriptive queries, objects, animals, or semantic concepts that users expect to find.
*Merged from*: Content Recognition Issues (run_2), Semantic & Object Search Failures (run_4)
*Example phrases*: "AI misidentifies objects in photos"; "Semantic search fails to match descriptive queries"; "Search for groundhog returns mislabeled category results"

**Search Result Limitations & Incomplete Matches**: Search returns unexpectedly small subsets of matching results, cannot be expanded as needed, or shows narrowing without expected results.
*Merged from*: Search Result Limitations (run_2), Search Result Limitations (run_3)
*Example phrases*: "Filter returns only one result instead of many matches"; "Search limited to one old photo instead of all museum visits"; "Results cannot be expanded"

**Multi-Criteria & Advanced Search Limitations**: Google Photos cannot combine multiple search filters, criteria, or advanced search operators in a single query.
*Merged from*: Filter & Sort Limitations (run_2), Search Filter Limitations (run_3), Multi-Criteria Search Limitations (run_4)
*Example phrases*: "Cannot combine person plus date plus exclusion criteria"; "Sort order discards applied search filters"; "No advanced search with multiple attributes"

**Content-Specific Filter Gaps**: Google Photos lacks built-in search or filtering options for specific content types, attributes, or features (tags, video-only, duplicates, etc.).
*Merged from*: Feature Availability Gaps (run_2), Content-Specific Search Filters (run_4)
*Example phrases*: "No tag support for filtering"; "Cannot filter search results to videos only"; "No built-in duplicate photo detection"

**Photo Display & UI Bugs**: Photos or features are not visible in the user interface even though the data exists, metadata is correct, or the feature should be available.
*Merged from*: Display/UI Issues (run_1), Navigation & Display Bugs (run_2), Content Visibility & Display Issues (run_4)
*Example phrases*: "Main Photos tab fails to display photos from specific date"; "Scrolling displays glitches or missing photos"; "Recently added filter missing from Android UI"

**Data Loss & Deletion Issues**: Photos have been deleted, corrupted, or permanently removed from Google Photos or cannot be recovered, and deletion behavior is unexpected.
*Merged from*: Data Loss (run_1), Storage & Deletion Issues (run_2), Content Missing/Deleted (run_3)
*Example phrases*: "Photos deleted from Google Photos and not in local storage"; "Deleting from Drive doesn't remove from Your photos"; "Data unrecoverable through normal search"

**Large Library Search Challenges**: Finding specific photos becomes impractical or impossible due to library size, lack of advanced search tools, or no reverse search capability.
*Merged from*: Large Library Search Challenges (run_4)
*Example phrases*: "Too many photos to manually browse"; "No reverse image search for library"; "Searching large library without identifying details is impractical"

**Export & Metadata Loss**: Downloading or exporting photos from Google Photos loses or does not preserve metadata, quality, original formatting, or annotations.
*Merged from*: Export & Metadata Limitations (run_4)
*Example phrases*: "Downloaded files lack JSON metadata"; "Export loses quality or original formatting"; "Shared files missing annotations or album structure"

**User Misunderstanding**: The user misunderstood a feature, setting, or search result rather than the feature itself being broken or malfunctioning.
*Merged from*: User Confusion & Misunderstanding (run_2)
*Example phrases*: "User thought free up space deletes backed-up files"; "Misunderstood feature behavior"; "User error rather than system failure"

## workaround

**Manual Browsing**: Physically scrolling through photos, albums, or timelines without using search functionality, either as a workaround for failed searches or as a deliberate alternative method.
*Merged from*: Manual Browsing (run_1, run_3, run_4); Visual Browsing by Attribute (run_2)
*Example phrases*: Manually scrolling through thousands of photos; Browsing the chronological timeline instead of searching; Clicking through albums one by one

**Search Query Modification**: Changing the search terms, phrasing, format, or syntax—including spelling variants, rephrasing, and special characters—to improve search results.
*Merged from*: Query Syntax Adjustment (run_1); Search Query Reformulation (run_2); Search Query Modification (run_3, run_4); Advanced Query Operators (run_2); Descriptive or Detailed Query (run_2); Exact Match Search (run_3)
*Example phrases*: Switching from "yellow truck" to "pickup truck"; Using quotation marks around filenames; Trying multiple misspellings until one works

**Interface or Platform Switching**: Accessing photos through a different device, app version, website interface, or platform (web vs. mobile, Google Photos vs. other services) to perform the same search successfully.
*Merged from*: Platform/Interface Switching (run_1); Alternative Platform or Device (run_2); Interface Selection (run_3); Alternative Search Interface (run_4); Device Switching (run_4)
*Example phrases*: Using photos.google.com instead of the mobile app; Switching to Classic Search; Using Apple Photos on iPad instead of Google Photos

**Settings or Feature Adjustment**: Enabling, disabling, or toggling specific app settings, preferences, or feature flags to restore previous functionality or improve search behavior.
*Merged from*: Feature Toggling (run_1); Settings or Feature Adjustment (run_2); Feature Toggle (run_3); Settings/Preferences Adjustment (run_3); Settings Adjustment (run_4)
*Example phrases*: Turning off Activity-based personalization; Disabling the Ask Photos/Gemini feature; Adjusting account settings to restore sort options

**Metadata Enhancement**: Adding, editing, or modifying photo descriptions, captions, tags, timestamps, or filenames to make photos more searchable or discoverable.
*Merged from*: Metadata Modification (run_1); Manual Metadata or Organization (run_2); Metadata Check (run_3); Manual Timestamp Recording (run_3); Metadata Enhancement (run_4)
*Example phrases*: Copying album titles into photo descriptions; Manually changing photo timestamps; Adding tags to make photos more findable

**Organizational Workaround**: Creating albums, manually organizing photos into collections, or using naming conventions to arrange and retrieve photos rather than relying on search.
*Merged from*: Album Creation/Organization (run_1); External Organization (run_3); Organizational Workaround (run_4)
*Example phrases*: Creating a dedicated album named "FindMe"; Manually adding filtered photos to a newly created album; Organizing photos by folder structure

**Attribute-Based Filtering**: Using built-in filters, preset categories, or feature-specific navigation (date ranges, location maps, face recognition, video type) instead of keyword search.
*Merged from*: Category/Filter Selection (run_1); Filter or Category Selection (run_2); Category Filter (run_3); Feature Filtering (run_4); Location-Based Search (run_1, run_3, run_4); Face/People Filtering (run_1); Face/People Search (run_3)
*Example phrases*: Clicking "Motion photos" from category suggestions; Using the face/people filter to narrow results; Navigating location heatmaps; Filtering by video type

**Text Recognition Search**: Using optical character recognition (OCR) to search for words or text visible within photos rather than relying on filenames or metadata.
*Merged from*: OCR/Text Search (run_1); Filename or Text Recognition Search (run_2); Text Recognition (run_3); OCR Text Search (run_4)
*Example phrases*: Searching for words appearing in photographed text; Using OCR to find text within images; Searching by exact OCR text like "kerokero"

**Temporal or Date-Based Navigation**: Finding photos by searching for specific dates, date ranges, or browsing through chronological views and Recently Added sections.
*Merged from*: Date-Based Retrieval (run_1); Temporal or Chronological Navigation (run_2); Date-Based Navigation (run_3); Recently Added View (run_3)
*Example phrases*: Searching for "Feb 2020"; Using the Recently Added section sorted by upload date; Typing "Recently Added" into search

**Visual or Image-Based Search**: Using visual search, image similarity matching, Google Lens, or searching by image appearance rather than text.
*Merged from*: Visual/Image-Based Search (run_1); Descriptive or Detailed Query (run_2); Image-Based Search (run_3)
*Example phrases*: Using Google Lens to search by image; Using image similarity matching; Querying descriptively with visual characteristics

**Sort Order or Display Adjustment**: Changing the sort order of results (most relevant to most recent) or using zoom and gesture controls to reveal hidden information like date separators.
*Merged from*: Sort or Result Order Adjustment (run_2); Sort Order Adjustment (run_3); Visual Zoom Technique (run_4); Interface Interaction Gesture (run_2)
*Example phrases*: Switching from most relevant to most recent; Using pinch-to-zoom on search results; Manually scrolling to the correct position in results

**Export, Download, or File Retrieval**: Downloading, exporting, or transferring photos outside Google Photos using Takeout, direct downloads, or file sharing.
*Merged from*: File Download/Export (run_1); File System or Export Workaround (run_2); File Export/Migration (run_3); Export and Retrieval (run_4)
*Example phrases*: Using Google Takeout to export photos; Downloading files via the three-dot menu; Migrating photos to alternative services

**Batch Selection or Bulk Operations**: Using multi-select functionality to select and perform operations on multiple photos at once rather than searching individually.
*Merged from*: Batch Selection/Bulk Operations (run_1); Batch Operations (run_4)
*Example phrases*: Using shift-click to select multiple photos; Multi-selecting and deleting screenshots in bulk; Batch-moving photos to albums

**System Refresh or Sync Troubleshooting**: Restarting, reinstalling, or re-syncing the app, device, or backup processes to resolve technical issues preventing photos from being searchable or appearing.
*Merged from*: Sync/Backup Troubleshooting (run_1); App Refresh or Reinstallation (run_2); Sync/Backup Reset (run_3); Temporal Strategy (run_4)
*Example phrases*: Uninstalling and reinstalling the app; Turning backup off and on again; Force-syncing via "Back up all" option; Restarting the device

**Content Re-indexing**: Deleting and re-uploading photos, renaming files, or re-importing content to trigger reindexing or restore visibility and searchability.
*Merged from*: Content Re-upload or Refresh (run_2)
*Example phrases*: Deleting photos and re-uploading from DCIM folder; Renaming files to trigger reindexing; Re-importing content to restore Memories visibility

**External Tracking or Help-Seeking**: Using external tools, notes, or reaching out to others (original uploaders, support, community) to locate photos rather than relying on search functionality.
*Merged from*: External Manual Tracking (run_1); Direct Contact or External Help (run_2); Manual Timestamp Recording (run_3)
*Example phrases*: Manually recording photo dates in a notepad app; Contacting the original uploader directly; Asking the community for help locating photos

**Waiting for Background Processing**: Deferring search attempts and waiting for the system to complete indexing, synchronization, or face recognition before retrying.
*Merged from*: Waiting or Delayed Indexing (run_2)
*Example phrases*: Waiting for backup to settle before retrying; Allowing indexing time to complete; Waiting a day for face recognition to process

**No Workaround Found**: Indicating that no successful workaround or solution has been identified, and the user is seeking help or acknowledging failure.
*Merged from*: No Workaround Found (run_1)
*Example phrases*: No effective workaround found; Asking if there is a fix; Unable to locate solutions online

# Tableau URL Redirection Script

This repository provides a client-side HTML/JavaScript solution to facilitate the transition from an on-premise Tableau Server to Tableau Cloud. As organizations migrate their data analytics platforms to the cloud, updating numerous embedded links that pointed to on-premise Tableau Server views becomes a significant challenge.

## Why This Script Is Necessary

1. **Seamless Transition**: Ensures users experience no disruption when accessing legacy links that previously led to on-premise Tableau Server views, by automatically redirecting to the new Tableau Cloud URLs.

2. **Reduced Manual Effort**: Avoids the overwhelming task of manually updating potentially hundreds or thousands of embedded URLs across various platforms and documents.

3. **Integrity of Links**: Maintains the integrity of existing documentation and applications that utilize embedded Tableau links, ensuring continued data access without interruption or user confusion.

## Limitations of Traditional Redirection Methods

In the context of migrating from an on-premise Tableau Server to Tableau Cloud, traditional methods such as DNS redirection or reverse proxy path rewriting are often inadequate due to the following reasons:

1. DNS redirection simply points a domain name to a different IP address and does not handle changes in URL paths or structures. Since Tableau Cloud URLs involve not only a change in the domain but also a modification in the path structure (especially with the addition of site paths and potentially different fragment identifiers), DNS redirection cannot manage these detailed changes.

2. Although reverse proxy servers are capable of rewriting URLs at the path level, they encounter a significant limitation with URLs that contain fragment identifiers (the part of the URL following the `#` symbol). Fragment identifiers are handled client-side by the browser and are not sent to the server. This means that any server-side solution like a reverse proxy cannot access or rewrite this part of the URL, making it impossible to perform the necessary redirections that involve changes in the fragment.

### Why JavaScript Redirection is Ideal

Given these limitations, a client-side JavaScript approach is necessary:

- **Client-Side Handling**: JavaScript operates in the browser and has access to the entire URL, including the fragment identifier. This allows it to dynamically alter the URL based on the fragment's contents.
- **Flexibility and Control**: It offers the flexibility to construct new URLs dynamically, accommodating complex changes in the URL structure required by Tableau Cloud.

## Overview

The script provided intercepts the page load, extracts the URL fragment, and constructs a new URL appropriate for the Tableau Cloud environment. This redirection happens seamlessly, enhancing the user experience during the transition period.

## Limitations

This **only** redirects dashboard view links, it does not redirect links to other content items or parts of the server UI, for example datasources, projects or workbooks. This is due to a unique content ID being included in these type of links which will not map to the same content on your Cloud instance.

## Usage

To implement this solution:

1. **Download the HTML file** from this repository.
2. **Open the file in a text editor** to modify the BASE_URL and SITE_PATH variables to fit your specific Tableau Cloud environment.
3. **Host the modified HTML file** on your web server at the location previously occupied by your Tableau Server, or configure your web server to serve this file for the old URLs.

### Customization

Update the following variables in the script based on your new Tableau Cloud setup:

- `BASE_URL`: Your Tableau Cloud's base URL, typically formatted like `https://10ax.online.tableau.com`.
- `SITE_PATH`: The site-specific path segment in your Tableau Cloud URL, such as `/site/YOUR_SITE_NAME`.

### Example of Customized Script

```javascript
window.onload = function () {
  var oldPath = window.location.hash;
  if (oldPath.startsWith("#")) {
    oldPath = oldPath.slice(1);
  }
  var newPath =
    "https://10ax.online.tableau.com/#/site/MyExampleSite/#" + oldPath;
  window.location.href = newPath;
};
```

### Testing

Ensure the redirection works as expected by:

- Visiting old URLs to see if you are correctly redirected to the corresponding new URLs without any user input.
- Testing with different types of URLs to confirm that all possible cases are handled effectively.

### Support

For any issues or queries regarding customization, please create an issue in this repository's Issues section.

### License

This project is licensed under the GNU General Public License - see the LICENSE file for details.

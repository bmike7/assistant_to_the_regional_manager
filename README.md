# Assistant To The Regional Manager

Number 2 agent that tattletales on you. Telling what a specific
author did on a given day, e.g.:

```
$ attrm tattletale [PROJECT] Mike 2025-10-28

{
  "project": "/some_repo",
  "day": "2025-10-28",
  "summary": "On 2025-10-28, Mike improved the security and management of the project by introducing a tool to help automate system administration, making the server's remote access more secure, applying new firewall protections, and setting up an automatic system to block people who try to break in repeatedly."
}
```

# Discord Event BOT
This is discord bot to create even channels

## Installation
### Creating the bot/application
* Go to [discord developer portal](https://discord.com/developers/applications) to create an application
* After selecting below settings on OAuth2 page copy the link in the 'scopes' section:
    * Scopes:
        * bot
    * Bot Permissions:
        * Manage Roles
        * Manage Channels
        * View Channels
        * Send Messages
        * Manage Messages
        * Embed Links
        * Read Message History
        * Use External Emojis
        * Add Reactions
* On the Bot page untick Public BOT
* On the Bot page make sure `Requires OAuth2 Code Grant` is unticked
* On the Bot page make sure `Presence Intent` and `Server Members Intent` are ticked
### Configuring Discord
* Create a category, for exampe `events` (this will be case sensitive)
    * Create a text channel, for example `event-creation` (bot doesn't look at this yet)
    * Create a text channel, for example `event-details`

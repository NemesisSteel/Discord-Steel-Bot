# Gateway

This is the process that is directly connected to discord. It uses [discord.py](http://github.com/rapptz/discord.py) python3's asyncio lib. The process pushes some discord events to redis queues (1 queue per event type). It also has an json-RPC implementation through http mainly to access voice functionalities.

### Event payload

<table>
    <tr>
        <th>Field</th>
        <th>Type</th>
        <th>Description</th>
    </tr>
    <tr>
        <td>type</td>
        <td>string</td>
        <td>The event type</td>
    </tr>
    <tr>
        <td>guild</td>
        <td>object</td>
        <td>The guild where the event happened</td>
    </tr>
    <tr>
        <td>ts</td>
        <td>string</td>
        <td>Timestamp of the event</td>
    </tr>
    <tr>
        <td>producer</td>
        <td>string</td>
        <td>The gateway shard id (format: gateway-{shard_id}-{shard_count})</td>
    </tr>
    <tr>
        <td>data</td>
        <td>object</td>
        <td>The data related to the event (optional)</td>
    </tr>
    <tr>
        <td>before</td>
        <td>object</td>
        <td>Old data in case of update events (optional)</td>
    </tr>
    <tr>
        <td>after</td>
        <td>object</td>
        <td>Basically "data" when update events (optional)</td>
    </tr>
</table>

### Available events

* MESSAGE_CREATE
* MESSAGE_DELETE
* MESSAGE_EDIT
* GUILD_READY
* GUILD_JOIN
* GUILD_REMOVE
* GUILD_UPDATE
* MEMBER_JOIN
* MEMBER_REMOVE


Each event is left-pushed in a redis queue named `discord.events.{EVENT_TYPE}`

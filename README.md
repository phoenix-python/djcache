# djcache

djcache is a small library that adds automatic caching layer to your django application.

### Benefits
1. It's implicit, which means that there's no need to rewrite your code to use it
2. Can cache all type of queries
3. Easy to install
4. Provides reliable invalidation technique

### Caveats
1. Use djcache only for projects/subsystems with high read/write ratio
* due to invalidation technique any write will logically invalidate all cached queries associated with given table
2. Currently supports only Redis as caching layer

## Installation & Use
Run next lines on startup:

    import djcache
    djcache.patch()

And that's it. From that moment all sql queries will be cached

## Design

Djcache patches django's sql compiler. On cache miss we store serialized db result in Redis.
It keeps track of all valid cached queries in redis hashes.
During db write djcache drops related redis set. This step logically invalidates all cached queries

## Customization

You can customize behavior by adding DJCACHE_OPTIONS to your settings

Here is an example

    DJCACHE_OPTIONS = {
        'TTL': 24 * 60 * 60,
        'REDIS_SETTINGS': {'db': 0},
    }

Valid options are:
    * `DISABLE_CACHE`. Set it to True to fallback to default(uncached) behavior.
    * `TTL` - time to live for cached db result
    * `REDIS_SETTINGS` - settings for redis connection
    * `DISABLE_INVALIDATION`. Set it to True to disable invalidation. Useful if you want to cache for short period of time and don't care about possible inconsistencies during that time window
    * `BLACKLISTED_CONNECTIONS`. Set of django connections for which you want to disable caching. Useful if you want to separate sql queries with bad hit rate
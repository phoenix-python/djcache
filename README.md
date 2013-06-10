# djcache

djcache adds auto caching to your django application. It's implicit(so You 
don't need to rewrite code to use it) and easy to install.
Currently supports only mysql as database and redis as cache engine

## Installation & Use

Run next lines when worker starts(for example, add them to urls.py)

        import djcache
        djcache.patch()

And that's it. From now all sql queries will be cached

## Invalidation

Djcache uses two strategies for correct invalidation of sql queries
First one doesn't depend on django(default behaviour). 
It's based on triggers and currently works only with MySQL 
For correct invalidation run once following code:

        import djcache
        djcache.create_invalidation_triggers()

Second one uses django signals for correct invalidation.
It can work with any relational database but can not invalidate data if it has changed outside of django

## Customization

You can customize behaviour of djcache by adding DJCACHE_OPTIONS to your settings

Here is an example
    
        DJCACHE_OPTIONS = {
            'DISABLE_CACHE': False, # you can disable caching by setting this parametr to True
            'TTL': 24 * 60 * 60 # time to live of cached request
            'REDIS_SETTINGS': {'db': 0}, # redis connection settings,
            'INVALIDATION': 0, # 0 for trigger invalidation, 1 for signal invalidation
        }

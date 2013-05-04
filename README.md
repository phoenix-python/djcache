# djcache

djcache adds auto caching to your django application. It's implicit(so You 
don't need to rewrite code to use it) and easy to install.
Currently supports only mysql as database and redis as cache engine

## Installation & Use

1.  Clone repository

2.  Go to folder with code and run
    
        make

3.  Run next lines when worker starts(for example, add them to urls.py)

        import djcache
        djcache.patch()

And that's it. From now all sql queries will be cached

## Customization

You can customize behaviour of djcache by adding DJCACHE_OPTIONS to your settings

Here is an example
    
        DJCACHE_OPTIONS = {
            'DISABLE_CACHE': False, # you can disable caching by setting this parametr to True
            'TABLES': ['game', 'tag', 'comment'], # list of tables that you want to invalidate properly
            'TTL': 24 * 60 * 60 # time to live of cached request
            'REDIS_SETTINGS': {'db': 0}, # redis connection settings
        }

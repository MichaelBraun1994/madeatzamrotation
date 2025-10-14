# Backend

## Image fetching

Fetch N posts
    filter posts with images
    get {postIds, messages, imageIds} // Includes no deleted posts
If fetching failed
    break to continue showing images if mattermost access failed
    
Remove posts not present in postIds
Remove images not present in imageIds

Foreach imageid
    is image not cached
        fetch imageIds

## Image storage

PostIds, Username, Message, imageIds

### Filestructure

/cache
    /postIdA
        meta.json
        /imgs
            imageIdA.jpg
            imageIdB.jpg
            ..

meta.json:
    username
    message

## Execution

twice a day fetch images
present postwise

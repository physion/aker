function (doc) {
    if(doc.type && doc.type === 'database-state') {
        if(doc.last_seq && doc.timestamp) {
            if(doc.database) {
                emit([doc.database, doc.timestamp], doc.last_seq);
            } else {
                emit([doc._id, doc.timestamp], doc.last_seq);
            }
        }
    }
}
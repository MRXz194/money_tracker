function deleteNote(noteId){
    fetch('/delete-note',{
        method : 'POST',
        body : JSON.stringify({noteId: noteId}),
    }).then((__res) =>{
        window.location.href ="/";
    })
}
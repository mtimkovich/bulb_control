$(':button').click((e) => {
    const name = e.target.id;

    $.post('/load', { name })
        .done(() => {
            alert(`Set the ${name} lights`);
        })
        .fail(() => {
            alert('Something went wrong :(');
        })
});

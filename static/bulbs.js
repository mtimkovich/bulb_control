function flash(type, message) {
  const element = $(`.alert-${type}`);
  element.text(message);
  element.slideDown().delay(5000).slideUp();
}

$(':button').click((e) => {
    const name = e.target.id;

    $.post('/load', { name })
        .done(() => {
            flash('success', `Set the ${name} lights`);
        })
        .fail(() => {
            flash('danger', 'Something went wrong :(');
        })
});

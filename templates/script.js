const selected = document.getElementById('status-selector');
    selected.addEventListener('change', ()=>{
    const profile = document.querySelectorAll('.items');
    profile.forEach((pro) => {
    const career = pro.querySelector('.p-details').textContent.includes(selected.value);
    pro.style.display = career ? 'block':'none'
})
})

                                                                                                                                
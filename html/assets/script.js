window.onload = () => {
    var pin = document.getElementById("pin");
    var naming = document.getElementById("naming");
    var name = document.getElementById("name");
    var amount = document.getElementById("amount");
    var flood = document.getElementById("flood");
    var text = document.getElementById("text");

    function checkMaxCaps()
    {
        if (naming.value == "capitalized")
        {
            var maxCaps = 1 << name.value.length;
            if (amount.value > maxCaps)
            {
                text.innerText = `Amount will be capped at ${maxCaps}.`;
                text.style.color = "red";
            }
            else
            {
                text.innerText = "";
                text.style.color = "black";
            }
        }
    }

    naming.onchange = () => {
        if (naming.value == "random")
        {
            name.disabled = true;
        }
        else
        {
            name.disabled = false;
            checkMaxCaps();
        }
    }

    amount.oninput = () => {checkMaxCaps()};
    name.oninput = () => {checkMaxCaps()};
        
    flood.onclick = async () => {
        var formData = new FormData();
        formData.append("pin", parseInt(pin.value));
        formData.append("naming", naming.value)
        formData.append("name", name.value);
        formData.append("amount", parseInt(amount.value));
        text.innerText = "Flooding in progress...";
        text.style.color = "green";
        var request = await fetch("/api/flood", {
            method: "POST",
            body: formData
        })
        response = await request.json();
        console.log(response.message);
        text.innerText = response.message;
        if (response.type == "error")
        {
            text.style.color = "red";
        }
    }
}
function generate(){

let product = document.getElementById("product").value
let quantity = document.getElementById("quantity").value

fetch("/predict",{
method:"POST",
headers:{
"Content-Type":"application/json"
},
body:JSON.stringify({
product:product,
quantity:quantity
})
})
.then(response => response.json())
.then(data => {

document.getElementById("price").innerText = data.price
document.getElementById("gst").innerText = data.gst
document.getElementById("discount").innerText = data.discount
document.getElementById("total").innerText = data.total

})

}
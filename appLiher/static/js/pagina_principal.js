const productos = [
    {
        id:"Vestido",
        titulo:"Vestido",
        imagen: [
            "../static/Img/img9.jpg",
            "",
            ""
        ], 
        categoria:{
            nombre:"Vestido",
            id:"Vestido"
        },
        precio:70000,
        descuento:14,
        informacion:[
            "",
            "",
            "",
            "",
            ".",
            ""
        ],
        envio: "Envío Gratis",
        stock:100,
        proveedor:"",
    },
    {
        id:"Blusa",
        titulo:"Blusa",
        imagen: [
            "../static/Img/img8.jpg",
            "",
            ""
        ], 
        categoria:{
            nombre:"Blusa",
            id:"Blusa"
        },
        precio:70000,
        descuento:14,
        informacion:[
            "",
            "",
            "",
            "",
            ".",
            ""
        ],
        envio: "Envío Gratis",
        stock:100,
        proveedor:""
    },
    {
        id:"Prendas",
        titulo:" Vestido",
        imagen: [
            "../static/Img/img10.jpg",
            "",
            ""
        ], 
        categoria:{
            nombre:"Prendas",
            id:"Prendas"
        },
        precio:111999,
        descuento:10,
        informacion:[
            "",
            "",
            "",
            "",
            ".",
            ""
        ],
        envio: 5000,
        stock:21,
        proveedor:"",
    },
    {
        id:"celular-04",
        titulo:"Short",
        imagen: [
            "../static/Img/img12.jpg",
            "",
            ""
        ], 
        categoria:{
            nombre:"Prendas",
            id:""
        },
        precio:122000,
        descuento:13,
        informacion:[
            "",
            "",
            "",
            "",
            ".",
            ""
        ],
        envio: "Envío Gratis",
        stock:21,
        proveedor:"",
    },
    {
        id:"celular-04",
        titulo:"Short",
        imagen: [
            "../static/Img/img13.jpg",
            "",
            ""
        ], 
        categoria:{
            nombre:"Prendas",
            id:""
        },
        precio:122000,
        descuento:13,
        informacion:[
            "",
            "",
            "",
            "",
            ".",
            ""
        ],
        envio: "Envío Gratis",
        stock:21,
        proveedor:"",
    },{
        id:"celular-04",
        titulo:"Short",
        imagen: [
            "../static/Img/img6.jpg",
            "",
            ""
        ], 
        categoria:{
            nombre:"Prendas",
            id:""
        },
        precio:122000,
        descuento:13,
        informacion:[
            "",
            "",
            "",
            "",
            ".",
            ""
        ],
        envio: "Envío Gratis",
        stock:21,
        proveedor:"",
    },{
        id:"",
        titulo:"Short",
        imagen: [
            "../static/Img/img9.jpg",
            "",
            ""
        ], 
        categoria:{
            nombre:"Prendas",
            id:""
        },
        precio:122000,
        descuento:13,
        informacion:[
            "",
            "",
            "",
            "",
            ".",
            ""
        ],
        envio: "Envío Gratis",
        stock:21,
        proveedor:"",
    },{
        id:"celular-04",
        titulo:"Short",
        imagen: [
            "../static/Img/img9.jpg",
            "",
            ""
        ], 
        categoria:{
            nombre:"Prendas",
            id:""
        },
        precio:122000,
        descuento:13,
        informacion:[
            "",
            "",
            "",
            "",
            ".",
            ""
        ],
        envio: "Envío Gratis",
        stock:21,
        proveedor:"",
    },

    

   
]


const contenedorProductos = document.querySelector("#contenedor-productos");


//función para mostrar todos los productos
function cargarProductos(productos){
    //Vaciamos el contenedor productos, 
    contenedorProductos.innerHTML = "";

    //Recorremos todo el arreglo de elementos
    productos.forEach(producto =>{
        //creamos un div para el elemento producto
        const div = document.createElement("div");
        div.classList.add("producto");

        //Determino como mostrar el tipo de envio
        let precio_envio = ""
        if(producto.envio != "Envío Gratis"){
            precio_envio = ""
        }else{
            precio_envio = producto.envio;
        }
        div.innerHTML = `
            <img src="${producto.imagen[0]}" alt="" class="producto-imagen">
            <div class="producto-detalles">
                <h3 class="producto-titulo">${producto.titulo}</h3>
                <p class="producto-precio">$ ${(producto.precio).toLocaleString()}<span class="descuento"> ${producto.descuento}% OFF</span></p>
                <p class="producto-tipo-envio">${precio_envio}</p>
            </div>
        `;

        //le agrego el id a dicho producto
        div.id = producto.id;
        contenedorProductos.append(div);
    })
}
//Llamamos a la función
cargarProductos(productos);



//Tomo los Botones de las categorías

//agregamos un eventlistener a cada boton de categoría
function asignarEventListenerBotonCategoria(){
    botonesCategorias.forEach(boton=> {
        boton.addEventListener("click", (e)=>{
    
            if(e.currentTarget.id != "todos"){
                //Filtro por id
                //e.currentTarget.id = hace referencia al id del boton donde hice clic
                const productosFiltrados = productos.filter(producto => producto.categoria.id === e.currentTarget.id);
    
                //colocamos el titulo de la sección
                //Debemos buscar el primer producto que coincida con la categoría seleccionada, para luego tomar el nombre de la categoria
                const productoCagegoria = productos.find(producto=> producto.categoria.id === e.currentTarget.id);
                tituloSeccion.innerHTML = productoCagegoria.categoria.nombre;
    
                cargarProductos(productosFiltrados);
               
            }else{
                cargarProductos(productos);
                tituloSeccion.innerHTML = "Todos los productos";
            }

            // Una vez que se han cargado los productos le asignamos a dichos productos un EventListenerPara llamar que al hacer clic se visualice la información de dicho producto.
            asignarEventListenerProductos();


        })
    });
}



//tomo el contenedor donde esta el producto
const contenedorProductoVisitado = document.querySelector("#contenedor-producto-visitado");

//Agrego a cada producto un eventListener onclikc para dirigirlo a la pàgina producto
function asignarEventListenerProductos(){
    const divsProductos = document.querySelectorAll(".producto");
    
    divsProductos.forEach(producto=>{
        producto.addEventListener("click", (e)=>{
            contenedorProductos.style.display = "none";
    
            // div para ver el producto
            const div = document.createElement("div");
            div.classList.add("producto-visitado");
            div.id = e.currentTarget.id;
    
            const prod = productos.find((producto) => producto.id === e.currentTarget.id);
            console.log(prod);
    
            div.innerHTML = `
            <span class="cerrar" onclick="cerrar()"> <i class="bi bi-x-circle"></i> </span>
            <div class="fotos-galeria">
            <div class="miniaturas">
                <img src="${prod.imagen[0]}" alt="" class="img-miniatura">
                <img src="${prod.imagen[1]}" alt="" class="img-miniatura">
                <img src="${prod.imagen[2]}" alt="" class="img-miniatura">
            </div>
            <div class="foto-principal">
                <img src="${prod.imagen[0]}" alt="" id="foto-principal">
            </div>
        </div>
        <div class="info-producto">
            <h2 class="titulo-producto">${prod.titulo}</h2>
    
            <p class="precio-producto">$ ${(prod.precio).toLocaleString()} <span class="descuento">${prod.descuento}% OFF</span></p>
    
            <span class="txt">Lo que tenes que saber de este producto</span>
            <ul id="listado-info">
    
            </ul>
        </div>
        <div class="info-compra">
            <span class="info-stock">Stock disponible</span>
            <span class="cantidad">Cantidad: 1 unidad <span class="stock">(${prod.stock} disponibles)</span> </span>
    
            <button class="btn-agregar-al-carrito" id="${prod.id}">Agregar al Carrito</button>
    
            <span class="vendedor">Vendido por <a href="#">${prod.proveedor}</a></span>
    
            <div class="beneficios">
                <div class="beneficio">
                    <div class="col">
                        <i class="bi bi-arrow-return-left"></i>
                    </div>
                    <div class="col">
                        <a href="#">Devolución Gratis</a> Tenes 30 días desde que lo recibis
                    </div>
                </div>
                <div class="beneficio">
                    <div class="col">
                        <i class="bi bi-shield-check"></i>
                    </div>
                    <div class="col">
                        <a href="#">Compra protegida</a> recibí el producto que esperabas o te devolvemos tu dinero.
                    </div>
                </div>
                <div class="beneficio">
                    <div class="col">
                        <i class="bi bi-trophy"></i>
                    </div>
                    <div class="col">
                        <a href="#">Mercado Puntos</a> Sumá 900 puntos.
                    </div>
                </div>
            </div>
    
        </div>
            `;
            
            contenedorProductoVisitado.append(div);
            contenedorProductoVisitado.style.display = "flex";
    
            const listadoInfo = document.querySelector("#listado-info")
            //Listado de descripciones del producto
            prod.informacion.forEach(info =>{
                const li = document.createElement("li");
                li.innerHTML = info;
                listadoInfo.append(li);
            })
    
         
         
    
        })
    })
}

asignarEventListenerProductos();


//--------------------------------------------------
//Funión para cerrar la ventana de productos
function cerrar(){
    contenedorProductoVisitado.innerHTML = "";
    contenedorProductos.style.display = "grid";
    contenedorProductoVisitado.style.display = "none";
}


   


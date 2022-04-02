// callByValue = (varOne, varTwo)=>{
//     console.log("Inside Call by Value Method");
//     varOne = 100;
//     varTwo = 200;
//     console.log("varOne =" + varOne +", varTwo =" +varTwo);
// }

// let varOne = 10;
// let varTwo = 20;

// console.log("Before Call by Value Method");
// console.log("varOne =" + varOne +", varTwo =" +varTwo); 
// callByValue(varOne, varTwo);
// console.log("After Call by Value Methoddddddddđ"); 
// console.log("varOne =" + varOne +", varTwo =" +varTwo); 


// callByReference = (varObj)=>{
//     // varObj = JSON.parse(JSON.stringify(varObj))
//     console.log("Inside Call by Reference Method: ", typeof varObj); 
//     varObj.a = 100; 
//     console.log(varObj); 
// }

// let varObj = {'a':1};
// console.log("Before Call by Reference Method"); 
// console.log(varObj);
// callByReference(varObj) 
// console.log("After Call by Reference Method"); 
// console.log(varObj);


object = {
    a: "bar",
    b: function(){
        self = this;
        console.log(this.a);
        console.log(self.a);
        ()=>{
            console.log(self.a);
            console.log(this.a);
            
        }
    }
}

// object.b();
var person = {
    firstName: "Anh",
    lastName: "Tranngoc",
    fullName: function() {
        // Việc sử dụng "this" cũng tương tự như việc sử dụng "he"
        // trong câu tiếng Anh ở trên.
        console.log(this.firstName + " " + this.lastName);
        // Chúng ta cũng có thể viết thế này.
        console.log(person.firstName + " " + person.lastName);
    }
}
// person.fullName()
// function sayHi() {
//     console.log(name);
//     console.log(age);
//     var name = "Lydia";
//     let age = 21;
//     console.log(name);
//     console.log(age);
// } 
// sayHi();
// console.log('name ', name);

for (var i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 1);
}
  
  for (let i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 1);
}
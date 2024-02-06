pragma solidity ^0.8.18;


contract Payment {
    address payable public owner;
    address payable public courier;
    address public customer;
    uint private price;
    bool private end = false;

    constructor(address c, uint p) {
        owner = payable(msg.sender);
        customer = c;
        price = p;
    }

    modifier notEnded() {
        require(end == false, "Closed.");
        _;
    }

    modifier allowedOnlyOnwer() {
        require(msg.sender == owner, "Allowed only to owner.");
        _;
    }

    modifier allowedOnlyCustomer() {
        require(msg.sender == customer, "Invalid customer account.");
        _;
    }

    modifier courierAdded() {
        require(courier != address(0), "Delivery not complete.");
        _;
    }

    modifier courierNotAdded(){
        require(courier == address(0), "Courier is already assigned.");
        _;
    }

     modifier orderMustBePaid() {
        require(
            address(this).balance == price,
            "Transfer not complete."
        );
        _;
    }

    modifier mustPayFully() {
        require(
            msg.value == price,
            "Insufficient funds."
        );
        _;
    }


    function pay() payable external notEnded allowedOnlyCustomer mustPayFully
    {
        require(
            address(this).balance == price,
            "Transfer already complete."
        );

    }

    function addCourier(address payable _courier) external notEnded orderMustBePaid courierNotAdded
    {
        courier = _courier;
    }

    function deliveryDone() external allowedOnlyCustomer notEnded  orderMustBePaid courierAdded
    {
        courier.transfer(address(this).balance * 20 / 100);
        owner.transfer(address(this).balance * 80 / 100);
        end = true;
    }

}
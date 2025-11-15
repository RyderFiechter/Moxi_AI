// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title StorageRegistry
 * @dev Registry for storage providers in the DePIN network
 * Allows providers to register, update storage availability, and set pricing
 */
contract StorageRegistry is Ownable, ReentrancyGuard {
    // Provider information
    struct Provider {
        address providerAddress;
        address paymentWallet;      // Wallet to receive payments
        uint256 storageGB;         // Available storage in GB
        uint256 pricePerGB;        // Price per GB per month (in wei)
        bool isActive;             // Whether provider is accepting storage requests
        uint256 registeredAt;     // Timestamp of registration
        uint256 lastUpdate;        // Timestamp of last storage update
    }

    // Mapping from provider address to provider info
    mapping(address => Provider) public providers;
    
    // List of all registered provider addresses
    address[] public providerList;
    
    // Mapping to check if address is registered
    mapping(address => bool) public isRegistered;
    
    // Minimum storage requirement (in GB)
    uint256 public minimumStorageGB;
    
    // Events
    event ProviderRegistered(
        address indexed provider,
        address indexed paymentWallet,
        uint256 storageGB,
        uint256 pricePerGB
    );
    
    event StorageUpdated(
        address indexed provider,
        uint256 newStorageGB
    );
    
    event PriceUpdated(
        address indexed provider,
        uint256 newPricePerGB
    );
    
    event PaymentWalletUpdated(
        address indexed provider,
        address indexed newPaymentWallet
    );
    
    event ProviderActivated(address indexed provider);
    event ProviderDeactivated(address indexed provider);

    constructor(uint256 _minimumStorageGB) Ownable(msg.sender) {
        minimumStorageGB = _minimumStorageGB;
    }

    /**
     * @dev Register a new storage provider
     * @param paymentWallet Address to receive payments
     * @param storageGB Available storage in GB
     * @param pricePerGB Price per GB per month (in wei)
     */
    function registerProvider(
        address paymentWallet,
        uint256 storageGB,
        uint256 pricePerGB
    ) external nonReentrant {
        require(!isRegistered[msg.sender], "StorageRegistry: Already registered");
        require(paymentWallet != address(0), "StorageRegistry: Invalid payment wallet");
        require(storageGB >= minimumStorageGB, "StorageRegistry: Storage below minimum");
        require(pricePerGB > 0, "StorageRegistry: Price must be greater than 0");

        providers[msg.sender] = Provider({
            providerAddress: msg.sender,
            paymentWallet: paymentWallet,
            storageGB: storageGB,
            pricePerGB: pricePerGB,
            isActive: true,
            registeredAt: block.timestamp,
            lastUpdate: block.timestamp
        });

        providerList.push(msg.sender);
        isRegistered[msg.sender] = true;

        emit ProviderRegistered(msg.sender, paymentWallet, storageGB, pricePerGB);
    }

    /**
     * @dev Update storage availability
     * @param storageGB New available storage in GB
     */
    function updateStorage(uint256 storageGB) external nonReentrant {
        require(isRegistered[msg.sender], "StorageRegistry: Not registered");
        require(storageGB >= minimumStorageGB, "StorageRegistry: Storage below minimum");

        providers[msg.sender].storageGB = storageGB;
        providers[msg.sender].lastUpdate = block.timestamp;

        emit StorageUpdated(msg.sender, storageGB);
    }

    /**
     * @dev Update price per GB
     * @param pricePerGB New price per GB per month (in wei)
     */
    function updatePrice(uint256 pricePerGB) external nonReentrant {
        require(isRegistered[msg.sender], "StorageRegistry: Not registered");
        require(pricePerGB > 0, "StorageRegistry: Price must be greater than 0");

        providers[msg.sender].pricePerGB = pricePerGB;

        emit PriceUpdated(msg.sender, pricePerGB);
    }

    /**
     * @dev Update payment wallet address
     * @param newPaymentWallet New payment wallet address
     */
    function updatePaymentWallet(address newPaymentWallet) external nonReentrant {
        require(isRegistered[msg.sender], "StorageRegistry: Not registered");
        require(newPaymentWallet != address(0), "StorageRegistry: Invalid payment wallet");

        address oldWallet = providers[msg.sender].paymentWallet;
        providers[msg.sender].paymentWallet = newPaymentWallet;

        emit PaymentWalletUpdated(msg.sender, newPaymentWallet);
    }

    /**
     * @dev Activate provider (opt-in to storage lending)
     */
    function activate() external {
        require(isRegistered[msg.sender], "StorageRegistry: Not registered");
        require(!providers[msg.sender].isActive, "StorageRegistry: Already active");

        providers[msg.sender].isActive = true;
        emit ProviderActivated(msg.sender);
    }

    /**
     * @dev Deactivate provider (opt-out of storage lending)
     */
    function deactivate() external {
        require(isRegistered[msg.sender], "StorageRegistry: Not registered");
        require(providers[msg.sender].isActive, "StorageRegistry: Already inactive");

        providers[msg.sender].isActive = false;
        emit ProviderDeactivated(msg.sender);
    }

    /**
     * @dev Get provider information
     * @param provider Address of the provider
     * @return Provider struct with all information
     */
    function getProviderInfo(address provider) external view returns (Provider memory) {
        require(isRegistered[provider], "StorageRegistry: Provider not registered");
        return providers[provider];
    }

    /**
     * @dev Get total number of registered providers
     * @return Number of providers
     */
    function getProviderCount() external view returns (uint256) {
        return providerList.length;
    }

    /**
     * @dev Get list of all provider addresses
     * @return Array of provider addresses
     */
    function getAllProviders() external view returns (address[] memory) {
        return providerList;
    }

    /**
     * @dev Get active providers only
     * @return Array of active provider addresses
     */
    function getActiveProviders() external view returns (address[] memory) {
        address[] memory activeProviders = new address[](providerList.length);
        uint256 count = 0;
        
        for (uint256 i = 0; i < providerList.length; i++) {
            if (providers[providerList[i]].isActive) {
                activeProviders[count] = providerList[i];
                count++;
            }
        }
        
        // Resize array to actual count
        address[] memory result = new address[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = activeProviders[i];
        }
        
        return result;
    }

    // Admin functions

    /**
     * @dev Set minimum storage requirement (only owner)
     * @param newMinimum New minimum storage in GB
     */
    function setMinimumStorage(uint256 newMinimum) external onlyOwner {
        minimumStorageGB = newMinimum;
    }

    /**
     * @dev Remove a provider (only owner, for moderation)
     * @param provider Address of provider to remove
     */
    function removeProvider(address provider) external onlyOwner {
        require(isRegistered[provider], "StorageRegistry: Provider not registered");
        isRegistered[provider] = false;
        delete providers[provider];
    }
}


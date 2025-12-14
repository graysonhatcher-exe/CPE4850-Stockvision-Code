import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:intl/intl.dart';

class PantryScreen extends StatefulWidget {
  const PantryScreen({super.key});

  @override
  State<PantryScreen> createState() => _PantryScreenState();
}

class _PantryScreenState extends State<PantryScreen> {
  final User? _currentUser = FirebaseAuth.instance.currentUser;
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _quantityController = TextEditingController();
  final List<String> categories = ['Meat', 'Fruit', 'Vegetable', 'Dairy', 'Grain', 'Other'];

  String _selectedCategory = 'Other';
  DateTime? _expirationDate;

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<QuerySnapshot>(
      stream: FirebaseFirestore.instance
          .collection('users')
          .doc(_currentUser!.uid)
          .collection('pantry')
          .orderBy('timestamp', descending: true)
          .snapshots(),
      builder: (context, snapshot) {
        if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
        final docs = snapshot.data!.docs;

        return Scaffold(
          body: ListView(
            padding: const EdgeInsets.all(16),
            children: docs.map((doc) {
              final data = doc.data() as Map<String, dynamic>;
              final name = data['name'] ?? 'Unnamed';
              final category = data['category'] ?? 'Other';
              final quantity = data['quantity'] ?? 1;
              final Timestamp? expTimestamp = data['expiration'];
              final expDate = expTimestamp?.toDate();

              // Highlight if expired
              final bool isExpired = expDate != null && expDate.isBefore(DateTime.now());

              return Card(
                color: isExpired ? Colors.red.shade100 : null,
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: Colors.blueGrey,
                    child: Text(category[0].toUpperCase(), style: const TextStyle(color: Colors.white)),
                  ),
                  title: Text(name),
                  subtitle: Text('Qty: $quantity | $category' +
                      (expDate != null ? ' | Exp: ${DateFormat.yMd().format(expDate)}' : '')),
                  trailing: IconButton(
                    icon: const Icon(Icons.delete),
                    onPressed: () => _deleteItem(doc.id),
                  ),
                  onTap: () => _editItemDialog(doc.id, data),
                ),
              );
            }).toList(),
          ),
          floatingActionButton: FloatingActionButton(
            onPressed: _addItemDialog,
            child: const Icon(Icons.add),
          ),
        );
      },
    );
  }

  Future<void> _deleteItem(String docId) async {
    await FirebaseFirestore.instance
        .collection('users')
        .doc(_currentUser!.uid)
        .collection('pantry')
        .doc(docId)
        .delete();
  }

  Future<void> _addItemDialog() async {
    _nameController.clear();
    _quantityController.clear();
    _selectedCategory = categories[0];
    _expirationDate = null;

    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Pantry Item'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: _nameController,
                decoration: const InputDecoration(hintText: 'Item Name'),
              ),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                initialValue: _selectedCategory,
                items: categories.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                onChanged: (val) {
                  if (val != null) setState(() => _selectedCategory = val);
                },
                decoration: const InputDecoration(hintText: 'Category'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _quantityController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(hintText: 'Quantity'),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: Text(_expirationDate == null
                        ? 'No Expiration Selected'
                        : 'Expires: ${DateFormat.yMd().format(_expirationDate!)}'),
                  ),
                  TextButton(
                    onPressed: () async {
                      final selected = await showDatePicker(
                        context: context,
                        initialDate: DateTime.now(),
                        firstDate: DateTime.now().subtract(const Duration(days: 365)),
                        lastDate: DateTime.now().add(const Duration(days: 365 * 5)),
                      );
                      if (selected != null) setState(() => _expirationDate = selected);
                    },
                    child: const Text('Select Date'),
                  )
                ],
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () async {
              final name = _nameController.text.trim();
              final quantity = int.tryParse(_quantityController.text.trim()) ?? 1;
              if (name.isEmpty) return;

              await FirebaseFirestore.instance
                  .collection('users')
                  .doc(_currentUser!.uid)
                  .collection('pantry')
                  .add({
                'name': name,
                'category': _selectedCategory,
                'quantity': quantity,
                'timestamp': FieldValue.serverTimestamp(),
                'expiration': _expirationDate != null ? Timestamp.fromDate(_expirationDate!) : null,
              });

              Navigator.pop(context);
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
  }

  Future<void> _editItemDialog(String docId, Map<String, dynamic> data) async {
    _nameController.text = data['name'] ?? '';
    _quantityController.text = (data['quantity'] ?? 1).toString();
    _selectedCategory = data['category'] ?? 'Other';
    _expirationDate = (data['expiration'] as Timestamp?)?.toDate();

    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Edit Pantry Item'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: _nameController, decoration: const InputDecoration(hintText: 'Item Name')),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                initialValue: _selectedCategory,
                items: categories.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                onChanged: (val) {
                  if (val != null) setState(() => _selectedCategory = val);
                },
                decoration: const InputDecoration(hintText: 'Category'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _quantityController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(hintText: 'Quantity'),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: Text(_expirationDate == null
                        ? 'No Expiration Selected'
                        : 'Expires: ${DateFormat.yMd().format(_expirationDate!)}'),
                  ),
                  TextButton(
                    onPressed: () async {
                      final selected = await showDatePicker(
                        context: context,
                        initialDate: _expirationDate ?? DateTime.now(),
                        firstDate: DateTime.now().subtract(const Duration(days: 365)),
                        lastDate: DateTime.now().add(const Duration(days: 365 * 5)),
                      );
                      if (selected != null) setState(() => _expirationDate = selected);
                    },
                    child: const Text('Select Date'),
                  )
                ],
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () async {
              final name = _nameController.text.trim();
              final quantity = int.tryParse(_quantityController.text.trim()) ?? 1;
              if (name.isEmpty) return;

              await FirebaseFirestore.instance
                  .collection('users')
                  .doc(_currentUser!.uid)
                  .collection('pantry')
                  .doc(docId)
                  .update({
                'name': name,
                'category': _selectedCategory,
                'quantity': quantity,
                'expiration': _expirationDate != null ? Timestamp.fromDate(_expirationDate!) : null,
              });

              Navigator.pop(context);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }
}

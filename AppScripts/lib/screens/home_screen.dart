import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:fl_chart/fl_chart.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final User? _currentUser = FirebaseAuth.instance.currentUser;
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _quantityController = TextEditingController();
  final TextEditingController _searchController = TextEditingController();

  final List<String> categories = [
    'Meat',
    'Fruit',
    'Vegetable',
    'Dairy',
    'Grain',
    'Other'
  ];

  String _searchTerm = '';
  final List<String> _tips = [
    'Store fruits and veggies separately to extend shelf life.',
    'Use airtight containers for grains and cereals.',
    'Keep dairy products in the coldest part of the fridge.',
    'Label leftovers with dates to avoid waste.',
    'Freeze meat if you won’t use it within 2 days.'
  ];

  @override
  void initState() {
    super.initState();
    _searchController.addListener(() {
      setState(() {
        _searchTerm = _searchController.text.toLowerCase();
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Pantry Home'),
      ),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            UserAccountsDrawerHeader(
              accountEmail: Text(_currentUser?.email ?? 'User'),
              accountName: const Text('My Pantry'),
            ),
            ListTile(
              leading: const Icon(Icons.home),
              title: const Text('Home'),
              onTap: () => Navigator.pop(context),
            ),
            ListTile(
              leading: const Icon(Icons.kitchen),
              title: const Text('Pantry'),
              onTap: () => Navigator.pop(context),
            ),
          ],
        ),
      ),
      body: StreamBuilder<QuerySnapshot>(
        stream: FirebaseFirestore.instance
            .collection('users')
            .doc(_currentUser!.uid)
            .collection('pantry')
            .orderBy('timestamp', descending: true)
            .snapshots(),
        builder: (context, snapshot) {
          if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
          final docs = snapshot.data!.docs;

          // Filter items based on search term
          final filteredDocs = docs.where((doc) {
            final data = doc.data() as Map<String, dynamic>;
            final name = data['name']?.toString().toLowerCase() ?? '';
            return name.contains(_searchTerm);
          }).toList();

          // Category counts for dashboard and pie chart
          final Map<String, int> categoryCounts = {};
          for (var doc in docs) {
            final data = doc.data() as Map<String, dynamic>;
            final category = data['category'] ?? 'Other';
            categoryCounts[category] = (categoryCounts[category] ?? 0) + 1;
          }

          final colors = [
            Colors.green,
            Colors.red,
            Colors.orange,
            Colors.blue,
            Colors.purple,
            Colors.brown,
            Colors.grey,
          ];
          int colorIndex = 0;

          final pieSections = categoryCounts.entries.map((e) {
            final color = colors[colorIndex % colors.length];
            colorIndex++;
            return PieChartSectionData(
              value: e.value.toDouble(),
              title: e.key,
              color: color,
              titleStyle: const TextStyle(fontSize: 12, color: Colors.white),
            );
          }).toList();

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Good ${_greeting()}, ${_currentUser.email ?? 'User'}!',
                  style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 16),

                // Search bar
                TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    hintText: 'Search pantry items...',
                    prefixIcon: const Icon(Icons.search),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
                const SizedBox(height: 16),

                // Tips section
                Card(
                  color: Colors.orange.shade100,
                  elevation: 3,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text(
                      _tips[(DateTime.now().day) % _tips.length],
                      style: const TextStyle(fontSize: 16),
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                // Dashboard cards
                Wrap(
                  spacing: 16,
                  runSpacing: 16,
                  children: categoryCounts.entries.map((entry) {
                    return Card(
                      elevation: 4,
                      child: SizedBox(
                        width: 140,
                        height: 80,
                        child: Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(entry.key, style: const TextStyle(fontWeight: FontWeight.bold)),
                              Text('${entry.value} items'),
                            ],
                          ),
                        ),
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 20),

                // Pie chart
                SizedBox(
                  height: 200,
                  child: PieChart(
                    PieChartData(
                      sections: pieSections,
                      sectionsSpace: 2,
                      centerSpaceRadius: 40,
                    ),
                  ),
                ),
                const SizedBox(height: 20),

                // Recent items with swipe-to-delete
                const Text('Recent Pantry Items', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                const SizedBox(height: 10),
                ...filteredDocs.map((doc) {
                  final data = doc.data() as Map<String, dynamic>;
                  final name = data['name'] ?? 'Unnamed';
                  final category = data['category'] ?? 'Other';
                  final quantity = data['quantity'] ?? 1;

                  return Dismissible(
                    key: Key(doc.id),
                    direction: DismissDirection.endToStart,
                    background: Container(
                      alignment: Alignment.centerRight,
                      padding: const EdgeInsets.only(right: 20),
                      color: Colors.red,
                      child: const Icon(Icons.delete, color: Colors.white),
                    ),
                    confirmDismiss: (direction) async {
                      return await showDialog(
                        context: context,
                        builder: (context) => AlertDialog(
                          title: const Text('Delete Item'),
                          content: Text('Are you sure you want to delete "$name"?'),
                          actions: [
                            TextButton(onPressed: () => Navigator.of(context).pop(false), child: const Text('Cancel')),
                            ElevatedButton(onPressed: () => Navigator.of(context).pop(true), child: const Text('Delete')),
                          ],
                        ),
                      );
                    },
                    onDismissed: (direction) async {
                      await FirebaseFirestore.instance
                          .collection('users')
                          .doc(_currentUser.uid)
                          .collection('pantry')
                          .doc(doc.id)
                          .delete();

                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('$name deleted')),
                      );
                    },
                    child: Card(
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: Colors.blueGrey,
                          child: Text(category[0].toUpperCase(), style: const TextStyle(color: Colors.white)),
                        ),
                        title: Text(name),
                        subtitle: Text('Qty: $quantity | $category'),
                      ),
                    ),
                  );
                }).toList(),
              ],
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _addItemDialog,
        child: const Icon(Icons.add),
      ),
    );
  }

  String _greeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'Morning';
    if (hour < 17) return 'Afternoon';
    return 'Evening';
  }

  Future<void> _addItemDialog() async {
    _nameController.clear();
    _quantityController.clear();
    String selectedCategory = categories[0];

    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Pantry Item'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _nameController,
              decoration: const InputDecoration(hintText: 'Item Name'),
            ),
            const SizedBox(height: 10),
            DropdownButtonFormField<String>(
              initialValue: selectedCategory,
              items: categories.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
              onChanged: (val) {
                if (val != null) selectedCategory = val;
              },
              decoration: const InputDecoration(hintText: 'Category'),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: _quantityController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(hintText: 'Quantity'),
            ),
          ],
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
                'category': selectedCategory,
                'quantity': quantity,
                'timestamp': FieldValue.serverTimestamp(),
              });

              Navigator.pop(context);
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
  }
}
